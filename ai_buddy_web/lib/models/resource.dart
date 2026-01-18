class Resource {
  final int id;
  final String title;
  final String description;
  final String url;
  final String category; // 'crisis', 'self_help', 'university'
  final String? country;
  final List<String> tags;

  Resource({
    required this.id,
    required this.title,
    required this.description,
    required this.url,
    required this.category,
    this.country,
    this.tags = const [],
  });

  factory Resource.fromJson(Map<String, dynamic> json) {
    return Resource(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      url: json['url'] ?? '',
      category: json['category'] ?? 'self_help',
      country: json['country'],
      tags: (json['tags'] as List?)?.map((e) => e.toString()).toList() ?? [],
    );
  }
}
