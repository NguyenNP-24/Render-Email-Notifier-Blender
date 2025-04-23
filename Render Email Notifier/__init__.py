bl_info = {
    "name": "Render Email Notifier",
    "author": "Nguyen Phuc Nguyen",
    "version": (1, 0, 2),
    "blender": (4, 3, 2),
    "location": "Render Properties > Email Notifier",
    "description": "Send mail with image preview after finish render",
    "category": "Render",
}

import bpy 
from . import notifier_core, ui_panel

def register():
    ui_panel.register()
    notifier_core.register_handlers()

def unregister():
    ui_panel.unregister()
    notifier_core.unregister_handlers()

if __name__ == "__main__":
    register()