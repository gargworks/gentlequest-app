"""
Resource API Routes for GentleQuest
Add these routes to app.py in _register_routes() function
"""

from flask import request, jsonify, current_app
from models import db
from sqlalchemy import text


def register_resource_routes(app):
    """Register resource-related API routes"""
    
    @app.route("/api/resources", methods=["GET"])
    @app.limiter.limit("60 per minute")
    def get_resources():
        """Get resources with optional filtering"""
        try:
            session_id = request.headers.get("X-Session-ID")
            if not session_id:
                return jsonify({"error": "Session ID required"}), 401
            
            category = request.args.get('category')
            country = request.args.get('country')
            search = request.args.get('search')
            
            # Build query
            where_clauses = ["is_active = true"]
            params = {}
            
            if category:
                where_clauses.append("category = :category")
                params['category'] = category
            
            if country:
                where_clauses.append("(country = :country OR country IS NULL)")
                params['country'] = country
            
            if search:
                where_clauses.append("""
                    (LOWER(title) LIKE :search 
                     OR LOWER(description) LIKE :search 
                     OR LOWER(tags) LIKE :search)
                """)
                params['search'] = f'%{search.lower()}%'
            
            where_sql = " AND ".join(where_clauses)
            
            resources = db.session.execute(
                text(f"""
                    SELECT id, title, description, url, category, country, tags
                    FROM resources
                    WHERE {where_sql}
                    ORDER BY created_at DESC
                    LIMIT 100
                """),
                params
            ).fetchall()
            
            resource_list = []
            for r in resources:
                resource_list.append({
                    'id': r[0],
                    'title': r[1],
                    'description': r[2],
                    'url': r[3],
                    'category': r[4],
                    'country': r[5],
                    'tags': r[6].split(',') if r[6] else []
                })
            
            return jsonify({
                "resources": resource_list,
                "count": len(resource_list)
            })
            
        except Exception as e:
            current_app.logger.error(f"Error fetching resources: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/api/resources/<int:resource_id>/view", methods=["POST"])
    @app.limiter.limit("60 per minute")
    def track_resource_view(resource_id):
        """Track that a user viewed a resource"""
        try:
            session_id = request.headers.get("X-Session-ID")
            if not session_id:
                return jsonify({"error": "Session ID required"}), 401
            
            # Verify resource exists
            resource = db.session.execute(
                text("SELECT id FROM resources WHERE id = :id"),
                {"id": resource_id}
            ).fetchone()
            
            if not resource:
                return jsonify({"error": "Resource not found"}), 404
            
            # Track view
            db.session.execute(
                text("""
                    INSERT INTO user_resource_interactions (session_id, resource_id)
                    VALUES (:session_id, :resource_id)
                """),
                {"session_id": session_id, "resource_id": resource_id}
            )
            db.session.commit()
            
            return jsonify({"success": True})
            
        except Exception as e:
            current_app.logger.error(f"Error tracking resource view: {e}")
            db.session.rollback()
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/api/admin/resources", methods=["GET", "POST", "PUT", "DELETE"])
    def admin_resources():
        """CRUD operations for resources (admin only)"""
        # TODO: Add admin authentication
        
        try:
            if request.method == "GET":
                resources = db.session.execute(
                    text("""
                        SELECT id, title, description, url, category, country, tags, is_active
                        FROM resources
                        ORDER BY created_at DESC
                    """)
                ).fetchall()
                
                resource_list = []
                for r in resources:
                    resource_list.append({
                        'id': r[0],
                        'title': r[1],
                        'description': r[2],
                        'url': r[3],
                        'category': r[4],
                        'country': r[5],
                        'tags': r[6].split(',') if r[6] else [],
                        'is_active': r[7]
                    })
                
                return jsonify({"resources": resource_list})
            
            elif request.method == "POST":
                data = request.get_json()
                
                result = db.session.execute(
                    text("""
                        INSERT INTO resources (title, description, url, category, country, tags)
                        VALUES (:title, :description, :url, :category, :country, :tags)
                        RETURNING id
                    """),
                    {
                        'title': data['title'],
                        'description': data['description'],
                        'url': data.get('url'),
                        'category': data['category'],
                        'country': data.get('country'),
                        'tags': data.get('tags', '')
                    }
                )
                resource_id = result.scalar()
                db.session.commit()
                
                return jsonify({"success": True, "id": resource_id}), 201
            
            elif request.method == "PUT":
                data = request.get_json()
                resource_id = data.get('id')
                
                if not resource_id:
                    return jsonify({"error": "Resource ID required"}), 400
                
                # Build update query dynamically
                updates = []
                params = {"id": resource_id}
                
                if 'title' in data:
                    updates.append("title = :title")
                    params['title'] = data['title']
                if 'description' in data:
                    updates.append("description = :description")
                    params['description'] = data['description']
                if 'url' in data:
                    updates.append("url = :url")
                    params['url'] = data['url']
                if 'is_active' in data:
                    updates.append("is_active = :is_active")
                    params['is_active'] = data['is_active']
                
                if updates:
                    db.session.execute(
                        text(f"UPDATE resources SET {', '.join(updates)} WHERE id = :id"),
                        params
                    )
                    db.session.commit()
                
                return jsonify({"success": True})
            
            elif request.method == "DELETE":
                resource_id = request.args.get('id')
                
                if not resource_id:
                    return jsonify({"error": "Resource ID required"}), 400
                
                # Soft delete
                db.session.execute(
                    text("UPDATE resources SET is_active = false WHERE id = :id"),
                    {"id": resource_id}
                )
                db.session.commit()
                
                return jsonify({"success": True})
                
        except Exception as e:
            current_app.logger.error(f"Admin resources error: {e}")
            db.session.rollback()
            return jsonify({"error": "Internal server error"}), 500
