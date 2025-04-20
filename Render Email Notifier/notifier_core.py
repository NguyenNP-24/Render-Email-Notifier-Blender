import bpy
import smtplib
import time
from email.message import EmailMessage
import os
from bpy.app.handlers import persistent

_render_start_time = None

# Get infos from scene.render_mailbot
def get_email_info(scene):
    sender = scene.render_mailbot.sender
    password = scene.render_mailbot.password
    
    if scene.render_mailbot.send_myself:
        recipients = [sender]
    else:
        recipients = [recipient.name for recipient in scene.render_mailbot.recipients if recipient.name.strip()]
        if not recipients:
            recipients = [sender]
            
    return sender, password, recipients

def send_email(subject, body, attachment=None):
    # Get infos gmail from scene.render_mailbot
    sender, password, recipients = get_email_info(bpy.context.scene)
    
    # Check
    if not sender or '@' not in sender:
        error_msg = "Invalid sender email"
        print(f"⚠️ {error_msg}")
        return False, error_msg
        
    if not recipients:
        error_msg = "No recipient email"
        print(f"⚠️ {error_msg}")
        return False, error_msg

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ", ".join(recipients)
    msg.set_content(body)

    if attachment and os.path.exists(attachment):
        try:
            with open(attachment, 'rb') as f:
                msg.add_attachment(f.read(), maintype='image', subtype='jpeg', filename='render_preview.jpg')
        except Exception as e:
            print(f"⚠️ Attach file error: {e}")

    try:
        # Use infos from UI
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
            success_msg = "📤 Mail has been sent!"
            print(success_msg)
            return True, success_msg
    except Exception as e:
        error_msg = f"Mail send error: {e}"
        print(f"⚠️ {error_msg}")
        try:
            bpy.ops.rendermailbot.show_message('INVOKE_DEFAULT', message=error_msg, icon='ERROR')
        except:
            pass  # If operator not regist
        return False, error_msg

def get_render_info():
    render = bpy.context.scene.render
    engine = render.engine
    
    # Engine render cases
    if engine == 'CYCLES':
        samples = bpy.context.scene.cycles.samples
    else:
        samples = "Not apply"
        
    return {
        'Resolution': f"{render.resolution_x}x{render.resolution_y}",
        'Frame Start': bpy.context.scene.frame_start,
        'Frame End': bpy.context.scene.frame_end,
        'Frame Current': bpy.context.scene.frame_current,
        'Samples': samples,
        'Render Engine': engine,
    }

def save_render_preview_as_jpg(path=None):
    if path is None:
        # Create dir 
        if os.name == 'nt':  # Windows
            path = os.path.join(os.environ.get('TEMP', 'C:\\Temp'), "render_preview.jpg")
        else:  # Linux/Mac
            path = "/tmp/render_preview.jpg"
    
    try:
        # Get render result
        image = bpy.data.images.get("Render Result")
        if not image:
            # Get result from viewport
            for window in bpy.context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == 'IMAGE_EDITOR':
                        image = area.spaces.active.image
                        break
        
        if image:
            image.save_render(path)
            print("✅ Saved preview at:", path)
            return path
        else:
            print("⚠️ Don't found Render Result")
    except Exception as e:
        print("⚠️ Save preview error:", e)
    
    return None

@persistent
def send_render_notification_later():
    global _render_start_time

    end_time = time.time()
    duration_sec = end_time - _render_start_time if _render_start_time else 0
    info = get_render_info()

    duration_str = time.strftime('%H:%M:%S', time.gmtime(duration_sec))
    body = f"""🎉 Render done!
- Render time: {duration_str} ({duration_sec:.2f} second)
- Resolutions: {info['Resolution']}
- Samples: {info['Samples']}
- Render Engine: {info['Render Engine']}
- Frame Range: {info['Frame Start']} đến {info['Frame End']}
- Frame Current: {info['Frame Current']}
"""

    print("Saving preview for sent mail...")
    preview_path = save_render_preview_as_jpg()
    print("Sending email notification of render completion...")
    success, msg = send_email("📸 Blender render done", body, preview_path)
    
    # Show messages in Blender interface if possible
    if success:
        try:
            bpy.ops.rendermailbot.show_message('INVOKE_DEFAULT', 
                                            message="📤 Mail sent successfully!", 
                                            icon='INFO')
        except Exception as e:
            print(f"Unable to display notification in UI: {e}")
            
    return None  # Only call once

@persistent
def on_render_start(scene):
    global _render_start_time
    _render_start_time = time.time()
    print("📸 Start Render - Start Timer")

@persistent
def on_render_complete(scene):
    print("🎉 Render complete - Register timer to send email")
    # Use shorter timeout
    bpy.app.timers.register(send_render_notification_later, first_interval=0.5)

@persistent
def on_render_error(scene):
    print("⚠️ Render Error - Sending Notification")
    send_email("⚠️ Blender render error", "Render was cancelled or encountered an unknown error.")

def register_handlers():
    # Handler persistent
    bpy.app.handlers.render_init.append(on_render_start)
    bpy.app.handlers.render_complete.append(on_render_complete)
    bpy.app.handlers.render_cancel.append(on_render_error)
    
    # Log debug
    print("📌 Register render email notifier!")
    print(f"  - render_init handler: {on_render_start.__name__}")
    print(f"  - render_complete handler: {on_render_complete.__name__}")
    print(f"  - render_cancel handler: {on_render_error.__name__}")

def unregister_handlers():
    # Delete handlers
    if on_render_start in bpy.app.handlers.render_init:
        bpy.app.handlers.render_init.remove(on_render_start)
    
    if on_render_complete in bpy.app.handlers.render_complete:
        bpy.app.handlers.render_complete.remove(on_render_complete)
    
    if on_render_error in bpy.app.handlers.render_cancel:
        bpy.app.handlers.render_cancel.remove(on_render_error)
    
    print("📌 Unregister render email notifier!")