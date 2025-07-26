#!/usr/bin/env python3
"""
Color and icon synchronization module for SuperProductivity dashboard.
"""

from typing import Dict, Any, Optional, Tuple


class ColorIconSync:
    """
    Handles synchronization of colors and icons between SuperProductivity and dashboard.
    """
    
    def __init__(self, data: Dict[str, Any]):
        """
        Initialize with SuperProductivity data.
        
        Args:
            data: The loaded SuperProductivity data
        """
        self.data = data
        self.project_colors = {}
        self.project_icons = {}
        self.tag_colors = {}
        self.tag_icons = {}
        self._extract_colors_and_icons()
    
    def _extract_colors_and_icons(self):
        """Extract colors and icons from projects and tags."""
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
        """
        Extract the primary color from an entity's theme.
        
        Args:
            entity: Project or tag entity
            
        Returns:
            str: Hex color code or default color
        """
        theme = entity.get('theme', {})
        if isinstance(theme, dict):
            primary_color = theme.get('primary', '')
            if primary_color and primary_color.startswith('#'):
                return primary_color
        
        # Default colors if no theme found
        return '#636efa'  # Default plotly blue
    
    def get_project_color(self, project_name: str) -> str:
        """
        Get the color for a project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            str: Hex color code
        """
        return self.project_colors.get(project_name, '#636efa')
    
    def get_project_icon(self, project_name: str) -> str:
        """
        Get the icon for a project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            str: Icon (emoji or icon name)
        """
        return self.project_icons.get(project_name, '📁')
    
    def get_tag_color(self, tag_name: str) -> str:
        """
        Get the color for a tag.
        
        Args:
            tag_name: Name of the tag
            
        Returns:
            str: Hex color code
        """
        return self.tag_colors.get(tag_name, '#636efa')
    
    def get_tag_icon(self, tag_name: str) -> str:
        """
        Get the icon for a tag.
        
        Args:
            tag_name: Name of the tag
            
        Returns:
            str: Icon (emoji or icon name)
        """
        return self.tag_icons.get(tag_name, '🏷️')
    
    def get_project_display_name(self, project_name: str) -> str:
        """
        Get the display name with icon for a project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            str: Project name with icon
        """
        icon = self.get_project_icon(project_name)
        return f"{icon} {project_name}"
    
    def get_tag_display_name(self, tag_name: str) -> str:
        """
        Get the display name with icon for a tag.
        
        Args:
            tag_name: Name of the tag
            
        Returns:
            str: Tag name with icon
        """
        icon = self.get_tag_icon(tag_name)
        return f"{icon} {tag_name}"
    
    def get_color_palette_for_projects(self, project_names: list) -> list:
        """
        Get a color palette for a list of projects.
        
        Args:
            project_names: List of project names
            
        Returns:
            list: List of hex color codes
        """
        colors = []
        for project in project_names:
            colors.append(self.get_project_color(project))
        return colors
    
    def get_color_palette_for_tags(self, tag_names: list) -> list:
        """
        Get a color palette for a list of tags.
        
        Args:
            tag_names: List of tag names
            
        Returns:
            list: List of hex color codes
        """
        colors = []
        for tag in tag_names:
            colors.append(self.get_tag_color(tag))
        return colors
    
    def print_sync_info(self):
        """Print information about synchronized colors and icons."""
        print("=== PROJECT COLORS AND ICONS ===")
        for project, color in self.project_colors.items():
            icon = self.project_icons.get(project, '')
            print(f"  {project}: {color} {icon}")
        
        print("\n=== TAG COLORS AND ICONS ===")
        for tag, color in self.tag_colors.items():
            icon = self.tag_icons.get(tag, '')
            print(f"  {tag}: {color} {icon}")


def create_color_sync(data: Dict[str, Any]) -> ColorIconSync:
    """
    Create a ColorIconSync instance.
    
    Args:
        data: SuperProductivity data
        
    Returns:
        ColorIconSync: Initialized color sync instance
    """
    return ColorIconSync(data)


if __name__ == "__main__":
    # Test the color sync
    from data_loader import load_super_productivity_data
    
    try:
        data = load_super_productivity_data()
        color_sync = create_color_sync(data['data'])
        color_sync.print_sync_info()
    except Exception as e:
        print(f"Error: {e}") 