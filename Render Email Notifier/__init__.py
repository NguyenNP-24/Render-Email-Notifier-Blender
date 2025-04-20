bl_info = {
    "name": "Render Email Notifier",
    "author": "Nguyen Phuc Nguyen",
    "version": (1, 0),
    "blender": (4, 3, 2),
    "location": "Render Properties > Email Notifier",
    "description": "Send mail with image preview after finish render",
    "category": "Render",
}

from . import notifier_core, ui_panel

def register():
    ui_panel.register()
    notifier_core.register_handlers()

def unregister():
    ui_panel.unregister()
    # Replace unregister_handlers call with direct code
    try:
        # Delete registered handlers
        for handler_list, handler_name in [
            (bpy.app.handlers.render_complete, "on_render_complete"),
            (bpy.app.handlers.render_cancel, "on_render_error"),
            (bpy.app.handlers.render_init, "on_render_start")
        ]:
            for handler in handler_list[:]:
                if hasattr(handler, "__name__") and handler.__name__ == handler_name:
                    handler_list.remove(handler)
        print("📌 Unregisted from render email notifier!")
    except Exception as e:
        print(f"Error while unregistering handler: {e}")

if __name__ == "__main__":
    register()