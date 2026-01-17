class Resource {
  final int id;
  final String title;
  final String description;
  final String? url;
  final String category;
  final String? country;
  final List<String> tags;

  Resource({
    required this.id,
    required this.title,
    required this.description,
    this.url,
    required this.category,
    this.country,
    required this.tags,
  });

  factory Resource.fromJson(Map<String, dynamic> json) {
    return Resource(
      id: json['id'] as int,
      title: json['title'] as String,
      description: json['description'] as String,
      url: json['url'] as String?,
      category: json['category'] as String,
      country: json['country'] as String?,
      tags: (json['tags'] as List?)?.cast<String>() ?? [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'url': url,
      'category': category,
      'country': country,
      'tags': tags,
    };
  }
}
