from typing import Dict, Any

class ColorIconSync:
    """
    Handles synchronization of colors and icons between SuperProductivity and dashboard.
    """
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.project_colors = {}
        self.project_icons = {}
        self.tag_colors = {}
        self.tag_icons = {}
        self._extract_colors_and_icons()

    def _extract_colors_and_icons(self):
        # Extract project colors and icons
        if 'project' in self.data and 'entities' in self.data['project']:
            for project_id, project in self.data['project']['entities'].items():
                title = project.get('title', '')
                self.project_colors[title] = self._extract_primary_color(project)
                self.project_icons[title] = project.get('icon', '')
        # Extract tag colors and icons
        if 'tag' in self.data and 'entities' in self.data['tag']:
            for tag_id, tag in self.data['tag']['entities'].items():
                title = tag.get('title', '')
                self.tag_colors[title] = self._extract_primary_color(tag)
                self.tag_icons[title] = tag.get('icon', '')

    def _extract_primary_color(self, entity: Dict[str, Any]) -> str:
        theme = entity.get('theme', {})
        if isinstance(theme, dict):
            primary_color = theme.get('primary', '')
            if primary_color and primary_color.startswith('#'):
                return primary_color
        return '#636efa'  # Default plotly blue

    def get_project_color(self, project_name: str) -> str:
        return self.project_colors.get(project_name, '#636efa')

    def get_project_icon(self, project_name: str) -> str:
        return self.project_icons.get(project_name, '📁')

    def get_tag_color(self, tag_name: str) -> str:
        return self.tag_colors.get(tag_name, '#636efa')

    def get_tag_icon(self, tag_name: str) -> str:
        return self.tag_icons.get(tag_name, '🏷️')

    def get_project_display_name(self, project_name: str) -> str:
        icon = self.get_project_icon(project_name)
        return f"{icon} {project_name}"

    def get_tag_display_name(self, tag_name: str) -> str:
        icon = self.get_tag_icon(tag_name)
        return f"{icon} {tag_name}"

    def get_color_palette_for_projects(self, project_names: list) -> list:
        return [self.get_project_color(project) for project in project_names]

    def get_color_palette_for_tags(self, tag_names: list) -> list:
        return [self.get_tag_color(tag) for tag in tag_names]

def create_color_sync(data: Dict[str, Any]) -> ColorIconSync:
    return ColorIconSync(data) 