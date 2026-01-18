"""
Resource API Routes for GentleQuest
Add these routes to app.py in _register_routes() function
"""

from flask import request, jsonify, current_app
from models import db, Resource, UserResourceInteraction
from sqlalchemy import or_


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
            
            # Start query with ORM
            query = Resource.query.filter_by(is_active=True)
            
            if category:
                query = query.filter(Resource.category == category)
            
            if country:
                query = query.filter(or_(Resource.country == country, Resource.country.is_(None)))
            
            if search:
                search_term = f"%{search.lower()}%"
                query = query.filter(
                    or_(
                        Resource.title.ilike(search_term),
                        Resource.description.ilike(search_term),
                        Resource.tags.ilike(search_term)
                    )
                )
            
            resources = query.order_by(Resource.created_at.desc()).limit(100).all()
            
            resource_list = []
            for r in resources:
                resource_list.append({
                    'id': r.id,
                    'title': r.title,
                    'description': r.description,
                    'url': r.url,
                    'category': r.category,
                    'country': r.country,
                    'tags': r.tags.split(',') if r.tags else []
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
            
            # Verify resource exists - Use ORM
            resource = Resource.query.get(resource_id)
            if not resource:
                return jsonify({"error": "Resource not found"}), 404
            
            # Track view
            interaction = UserResourceInteraction(
                session_id=session_id,
                resource_id=resource_id
            )
            db.session.add(interaction)
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
                resources = Resource.query.order_by(Resource.created_at.desc()).all()
                
                resource_list = []
                for r in resources:
                    resource_list.append({
                        'id': r.id,
                        'title': r.title,
                        'description': r.description,
                        'url': r.url,
                        'category': r.category,
                        'country': r.country,
                        'tags': r.tags.split(',') if r.tags else [],
                        'is_active': r.is_active
                    })
                
                return jsonify({"resources": resource_list})
            
            elif request.method == "POST":
                data = request.get_json()
                
                resource = Resource(
                    title=data['title'],
                    description=data['description'],
                    url=data.get('url'),
                    category=data['category'],
                    country=data.get('country'),
                    tags=data.get('tags', '')
                )
                db.session.add(resource)
                db.session.commit()
                
                return jsonify({"success": True, "id": resource.id}), 201
            
            elif request.method == "PUT":
                data = request.get_json()
                resource_id = data.get('id')
                
                if not resource_id:
                    return jsonify({"error": "Resource ID required"}), 400
                
                resource = Resource.query.get(resource_id)
                if not resource:
                    return jsonify({"error": "Resource not found"}), 404
                
                if 'title' in data:
                    resource.title = data['title']
                if 'description' in data:
                    resource.description = data['description']
                if 'url' in data:
                    resource.url = data['url']
                if 'is_active' in data:
                    resource.is_active = data['is_active']
                
                db.session.commit()
                return jsonify({"success": True})
            
            elif request.method == "DELETE":
                resource_id = request.args.get('id')
                
                if not resource_id:
                    return jsonify({"error": "Resource ID required"}), 400
                
                resource = Resource.query.get(resource_id)
                if not resource:
                    return jsonify({"error": "Resource not found"}), 404
                
                # Soft delete
                resource.is_active = False
                db.session.commit()
                
                return jsonify({"success": True})
                
        except Exception as e:
            current_app.logger.error(f"Admin resources error: {e}")
            db.session.rollback()
            return jsonify({"error": "Internal server error"}), 500
