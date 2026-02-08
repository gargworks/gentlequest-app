require 'xcodeproj'

project_path = 'ai_buddy_web/ios/Runner.xcodeproj'
puts "Opening project at #{project_path}"
project = Xcodeproj::Project.open(project_path)

# Find the Runner group
runner_group = project.main_group.find_subpath('Runner')
if runner_group.nil?
  puts "Error: Could not find 'Runner' group"
  exit 1
end

# Check if file ref exists
file_name = 'GoogleService-Info.plist'
file_ref = runner_group.find_file_by_path(file_name)

if file_ref
  puts "Found existing file reference for #{file_name}"
else
  puts "Creating file reference for #{file_name}"
  # "Runner/GoogleService-Info.plist" is the path relative to source root usually, 
  # or if added to Runner group it might be just the name if the group has a path.
  # SAFEST: Add it to the group.
  file_ref = runner_group.new_reference(file_name)
end

# Find the target
target = project.targets.find { |t| t.name == 'Runner' }
if target.nil?
  puts "Error: Could not find 'Runner' target"
  exit 1
end

# Add to Copy Bundle Resources
resources_phase = target.resources_build_phase
existing_build_file = resources_phase.files.find { |bf| bf.file_ref && bf.file_ref.path == file_name }

if existing_build_file
  puts "#{file_name} is already in Copy Bundle Resources phase"
else
  puts "Adding #{file_name} to Copy Bundle Resources phase"
  resources_phase.add_file_reference(file_ref)
  project.save
  puts "Project saved successfully"
end
