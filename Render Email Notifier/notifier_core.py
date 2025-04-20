import bpy
import smtplib
import time
from email.message import EmailMessage
import os
from bpy.app.handlers import persistent

# Global variables to track render state
_render_start_time = None  # Stores when rendering began
_email_sent = False        # Flag to prevent duplicate emails
_render_in_progress = False # Track if we're currently rendering

def get_email_info(scene):
    """Retrieve email configuration from scene properties"""
    sender = scene.render_mailbot.sender
    password = scene.render_mailbot.password
    
    # Determine recipients - either sender or recipient list
    if scene.render_mailbot.send_myself:
        recipients = [sender]
    else:
        recipients = [recipient.name for recipient in scene.render_mailbot.recipients if recipient.name.strip()]
        if not recipients:  # Fallback to sender if no recipients
            recipients = [sender]
            
    return sender, password, recipients

def send_email(subject, body, attachment=None):
    """Send email with render results"""
    sender, password, recipients = get_email_info(bpy.context.scene)
    
    # Validate sender email
    if not sender or '@' not in sender:
        error_msg = "Invalid sender email"
        print(f"⚠️ {error_msg}")
        return False, error_msg
        
    if not recipients:
        error_msg = "No recipient email"
        print(f"⚠️ {error_msg}")
        return False, error_msg

    # Prepare email message
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ", ".join(recipients)
    msg.set_content(body)

    # Add attachment if provided and exists
    if attachment and os.path.exists(attachment):
        try:
            with open(attachment, 'rb') as f:
                msg.add_attachment(f.read(), maintype='image', subtype='jpeg', filename='render_preview.jpg')
        except Exception as e:
            print(f"⚠️ Failed to attach file: {e}")

    # Send email via SMTP
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
            success_msg = "📤 Email sent successfully!"
            print(success_msg)
            return True, success_msg
    except Exception as e:
        error_msg = f"Failed to send email: {e}"
        print(f"⚠️ {error_msg}")
        try:
            bpy.ops.rendermailbot.show_message('INVOKE_DEFAULT', message=error_msg, icon='ERROR')
        except:
            pass  # Fallback if operator isn't available
        return False, error_msg

def get_render_info():
    """Collect render statistics and settings"""
    render = bpy.context.scene.render
    engine = render.engine
    
    # Get samples count based on render engine
    samples = bpy.context.scene.cycles.samples if engine == 'CYCLES' else "N/A"
        
    return {
        'Resolution': f"{render.resolution_x}x{render.resolution_y}",
        'Frame Start': bpy.context.scene.frame_start,
        'Frame End': bpy.context.scene.frame_end,
        'Frame Current': bpy.context.scene.frame_current,
        'Samples': samples,
        'Render Engine': engine,
    }

def save_render_preview_as_jpg(path=None):
    """Save render result as temporary JPG for email attachment"""
    if path is None:
        # Use system temp directory
        path = os.path.join(os.environ.get('TEMP', '/tmp'), "render_preview.jpg")
    
    try:
        # Try to get render result from image editor
        image = bpy.data.images.get("Render Result")
        if not image:
            for window in bpy.context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == 'IMAGE_EDITOR':
                        image = area.spaces.active.image
                        break
        
        if image:
            image.save_render(path)
            print("✅ Preview saved at:", path)
            return path
        else:
            print("⚠️ No render result found")
    except Exception as e:
        print("⚠️ Failed to save preview:", e)
    
    return None

@persistent
def send_render_notification_later():
    """Callback to send notification after short delay"""
    global _email_sent, _render_in_progress
    
    # Only send if we haven't already and render was in progress
    if _email_sent or not _render_in_progress:
        return None
        
    _email_sent = True  # Mark email as sent
    _render_in_progress = False  # Render is complete
    
    end_time = time.time()
    duration_sec = end_time - _render_start_time if _render_start_time else 0
    info = get_render_info()

    # Format duration as HH:MM:SS
    duration_str = time.strftime('%H:%M:%S', time.gmtime(duration_sec))
    
    # Prepare email body with render info
    body = f"""🎉 Render Complete!
- Duration: {duration_str} ({duration_sec:.2f} seconds)
- Resolution: {info['Resolution']}
- Samples: {info['Samples']}
- Engine: {info['Render Engine']}
- Frame Range: {info['Frame Start']} to {info['Frame End']}
- Current Frame: {info['Frame Current']}
"""

    print("Saving render preview...")
    preview_path = save_render_preview_as_jpg()
    print("Sending completion email...")
    success, msg = send_email("📸 Blender Render Complete", body, preview_path)
    
    # Show UI notification if possible
    if success:
        try:
            bpy.ops.rendermailbot.show_message('INVOKE_DEFAULT', 
                                            message="📤 Email sent successfully!", 
                                            icon='INFO')
        except Exception as e:
            print(f"Couldn't show UI notification: {e}")
            
    return None  # Only run once

@persistent
def on_render_start(scene):
    """Handler for render start event"""
    global _render_start_time, _email_sent, _render_in_progress
    
    # Reset state for new render
    _render_start_time = time.time()
    _email_sent = False
    _render_in_progress = True
    print("⏱️ Render started - timer reset")

@persistent
def on_render_complete(scene):
    """Handler for render completion"""
    global _render_in_progress
    
    if not _render_in_progress:
        return
        
    print("✅ Render complete - scheduling email")
    # Schedule email with small delay to ensure everything is ready
    bpy.app.timers.register(send_render_notification_later, first_interval=0.5)

@persistent
def on_render_cancel(scene):
    """Handler for render cancellation/error"""
    global _email_sent, _render_in_progress
    
    if _email_sent or not _render_in_progress:
        return
        
    _email_sent = True
    _render_in_progress = False
    print("⚠️ Render cancelled - sending notification")
    send_email("⚠️ Blender Render Cancelled", "The render was cancelled or encountered an error.")

def register_handlers():
    """Register our handlers with Blender"""
    # Remove any existing handlers first to prevent duplicates
    unregister_handlers()
    
    # Add our persistent handlers
    bpy.app.handlers.render_init.append(on_render_start)
    bpy.app.handlers.render_complete.append(on_render_complete)
    bpy.app.handlers.render_cancel.append(on_render_cancel)
    
    print("🔔 Registered render notification handlers")

def unregister_handlers():
    """Clean up all our handlers"""
    handlers = [
        (bpy.app.handlers.render_init, on_render_start),
        (bpy.app.handlers.render_complete, on_render_complete),
        (bpy.app.handlers.render_cancel, on_render_cancel)
    ]
    
    for handler_list, func in handlers:
        if func in handler_list:
            handler_list.remove(func)
    
    print("🔕 Unregistered render notification handlers")