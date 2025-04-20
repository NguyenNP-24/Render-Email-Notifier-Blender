import bpy
from bpy.types import Panel, Operator
from bpy.props import StringProperty, BoolProperty, CollectionProperty, PointerProperty


# Email checking function
def validate_email(self, context):
    email = self.sender
    if email and ('@' not in email or '.' not in email):
        self.sender = ""  # Delete invalid email
        try:
            bpy.ops.rendermailbot.show_message('INVOKE_DEFAULT', 
                                            message="Please enter a valid email address",
                                            icon='ERROR')
        except:
            pass  # If the operator is not registered

# Class to store recipient email
class RecipientItem(bpy.types.PropertyGroup):
    name: StringProperty(
        name="Email",
        description="Recipient's email",
        default=""
    )

# Update when 'Send Myself' toggle changes - no need to modify list
def update_send_myself(self, context):
    pass  # Processing logic in get_email_info() function

class RenderMailBotProperties(bpy.types.PropertyGroup):
    sender: StringProperty(
        name="Sender Email",
        description="Your email address",
        default="",
        maxlen=256,
        update=validate_email
    )
    password: StringProperty(
        name="Email Password",
        description="Your email app password (for Gmail, generated from Google account settings)",
        default="",
        maxlen=256,
        subtype='PASSWORD'
    )
    recipients: CollectionProperty(
        type=RecipientItem,
        name="Recipients",
        description="Email recipient list",
    )
    send_myself: BoolProperty(
        name="Send Myself",
        description="Send to yourself only",
        default=False,
        update=update_send_myself
    )

# Main Panel
class RenderMailBotPanel(Panel):
    bl_label = "Render Mail Notifier Settings"
    bl_idname = "RENDERMAILBOT_PT_main"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_category = "Render"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Email sender and password fields
        layout.prop(scene.render_mailbot, "sender")
        layout.prop(scene.render_mailbot, "password")

        # Toggle for "Send Myself"
        layout.prop(scene.render_mailbot, "send_myself")

        # Recipients input field
        if not scene.render_mailbot.send_myself:
            row = layout.row()
            row.label(text="Recipients:")
            for i, recipient in enumerate(scene.render_mailbot.recipients):
                row = layout.row(align=True)
                row.prop(recipient, "name", text="")
                op = row.operator("rendermailbot.remove_specific_recipient", text="", icon='X')
                op.index = i

        # Buttons to add/remove recipients
        row = layout.row()
        row.operator("rendermailbot.add_recipient", text="Add Recipient")
        
        # Test email button
        row = layout.row()
        row.operator("rendermailbot.test_email", text="Test Email")

# Operators for adding and removing recipients
class AddRecipientOperator(Operator):
    bl_idname = "rendermailbot.add_recipient"
    bl_label = "Add Recipient"
    bl_description = "Add more recipient"

    def execute(self, context):
        context.scene.render_mailbot.recipients.add()
        return {'FINISHED'}

class RemoveSpecificRecipientOperator(Operator):
    bl_idname = "rendermailbot.remove_specific_recipient"
    bl_label = "Remove Specific Recipient"
    bl_description = "Remove this recipient"
    
    index: bpy.props.IntProperty()

    def execute(self, context):
        if len(context.scene.render_mailbot.recipients) > self.index:
            context.scene.render_mailbot.recipients.remove(self.index)
        return {'FINISHED'}

# Operator to show notify
class ShowMessageOperator(Operator):
    bl_idname = "rendermailbot.show_message"
    bl_label = "Notification"
    
    message: StringProperty()
    icon: StringProperty(default='INFO')
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.label(text=self.message, icon=self.icon)

# Operator to test sent mail
class TestEmailOperator(Operator):
    bl_idname = "rendermailbot.test_email"
    bl_label = "Test Email"
    bl_description = "Send a test email to check system"
    
    def execute(self, context):
        from . import notifier_core
        
        subject = "🧪 Blender Email Notifier - Test"
        body = """This is email test from Blender Render Email Notifier Add-on.
        
If you receive this email, the add-on has been successfully installed and can send an email after rendering is complete.

Happy rendering! 😊
"""
        success, msg = notifier_core.send_email(subject, body)
        
        if success:
            self.report({'INFO'}, "Test email sent successfully!")
        else:
            self.report({'ERROR'}, f"Error sending email: {msg}")
            
        return {'FINISHED'}

# Register and unregister classes
classes = [
    RecipientItem,
    RenderMailBotProperties,
    RenderMailBotPanel,
    AddRecipientOperator,
    RemoveSpecificRecipientOperator,
    ShowMessageOperator,
    TestEmailOperator
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.render_mailbot = PointerProperty(type=RenderMailBotProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.render_mailbot

if __name__ == "__main__":
    register()