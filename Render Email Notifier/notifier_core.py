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
_is_animation = False      # Flag for animation render

def check_online_access():
    """Check if 'Allow Online Access' is enabled in Preferences"""
    try:
        if not bpy.context.preferences.system.use_online_access:
            def show_warning(self, context):
                self.layout.label(text="❗ 'Allow Online Access' is disabled.", icon='ERROR')
                self.layout.label(text="Please enable it in Preferences > System > Network.")

            bpy.context.window_manager.popup_menu(show_warning, title="Network Access Disabled", icon='INFO')
            return False
        return True
    except:
        return False

def get_email_info(scene):
    """Retrieve email configuration from scene properties"""
    sender = scene.render_mailbot.sender
    password = scene.render_mailbot.password
    
    # Determine recipients - either sender or recipient list
    if scene.render_mailbot.send_myself:
        recipients = [sender]
    else:
        recipients = [recipient.name for recipient in scene.render_mailbot.recipients if recipient.name.strip()]
        if not recipients: 
            raise ValueError("Error: No recipients found. Please add at least one recipient or enable 'Send to myself' option.")
            
    return sender, password, recipients

def send_email(subject, body, attachment=None):
    """Send email with render results"""
    print("📧 Attempting to send email...")

    # Check if Allow online access is enabled in Preference
    if not check_online_access():
        return False, "Online access is disabled."

    try:
        sender, password, recipients = get_email_info(bpy.context.scene)
        print(f"📧 Sender: {sender}, Recipients: {recipients}")
    except Exception as e:
        error_msg = f"Failed to get email info: {str(e)}"
        print(f"⚠️ {error_msg}")
        return False, error_msg
    
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
            print(f"📎 Attaching file: {attachment}")
            with open(attachment, 'rb') as f:
                msg.add_attachment(f.read(), maintype='image', subtype='jpeg', filename='render_preview.jpg')
        except Exception as e:
            print(f"⚠️ Failed to attach file: {e}")
    else:
        print("📄 No attachment or file doesn't exist")

    # Send email via SMTP
    try:
        print("🔌 Connecting to SMTP server...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            try:
                print("🔑 Attempting login...")
                smtp.login(sender, password)
                print("✅ Login successful")
            except smtplib.SMTPAuthenticationError as e:
                error_msg = f"Authentication failed: {str(e)}"
                print(f"⚠️ {error_msg}")
                return False, "Authentication failed. Check your email and app password."
        
            try:
                print("📤 Sending message...")
                smtp.send_message(msg)
                success_msg = "📤 Email sent successfully!"
                print(success_msg)
                
                # Clean up the preview image in save folder after sending
                if attachment and os.path.exists(attachment):
                    try:
                        os.remove(attachment)
                        print(f"🗑️ Cleaned up temporary file: {attachment}")
                    except Exception as e:
                        print(f"⚠️ Failed to delete temporary file: {e}")
                        
                return True, success_msg
            except Exception as e:
                error_msg = f"Failed to send message: {str(e)}"
                print(f"⚠️ {error_msg}")
                return False, error_msg
    except ConnectionError as e:
        error_msg = f"Connection error: {str(e)}"
        print(f"⚠️ {error_msg}")
        return False, "Connection error. Please check your internet connection."
    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        print(f"⚠️ {error_msg}")
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
    print("🖼️ Attempting to save render preview...")
    
    if path is None:
        # Use Blender's user resource folder (C:\Users\Hi\AppData\Roaming\Blender Foundation\Blender\version\datafiles\render_email_notifier)
        ext_dir = bpy.utils.user_resource('DATAFILES', path="render_email_notifier", create=True)
        path = os.path.join(ext_dir, "render_preview.jpg")
        print(f"📁 Using path: {path}")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # DIFFERENT APPROACH: Try to access the render result directly from the render context
    try:
        print("📷 Trying to save directly from current render...")
        bpy.ops.render.render_view_save(filepath=path)
        
        # Check if file was created
        if os.path.exists(path) and os.path.getsize(path) > 0:
            print(f"✅ Preview saved successfully: {path} ({os.path.getsize(path)} bytes)")
            return path
    except Exception as e:
        print(f"⚠️ Could not save directly: {e}")
    
    # Fallback
    try:
        image = bpy.data.images.get("Render Result")
        if image and hasattr(image, 'has_data') and image.has_data:
            print("✅ Using default Render Result")
            image.save_render(path)
            
            if os.path.exists(path) and os.path.getsize(path) > 0:
                print(f"✅ Preview saved successfully: {path}")
                return path
    except Exception as e:
        print(f"⚠️ Error with default approach: {e}")
    
    try:
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'IMAGE_EDITOR':
                    space_image = area.spaces.active
                    if space_image and space_image.image:
                        img = space_image.image
                        if img and img.has_data:
                            print(f"📷 Found image in editor: {img.name}")
                            img.save_render(path)
                            
                            if os.path.exists(path) and os.path.getsize(path) > 0:
                                print(f"✅ Preview saved successfully: {path}")
                                return path
    except Exception as e:
        print(f"⚠️ Error with image editor approach: {e}")
    
    print("All methods failed to save preview")
    return None

@persistent
def send_render_notification_later():
    """Callback to send notification after short delay"""
    global _email_sent, _render_in_progress, _is_animation
    
    # Only send if we haven't already and render was in progress
    if _email_sent or not _render_in_progress:
        return None
        
    _email_sent = True  # Mark email as sent
    _render_in_progress = False  # Render is complete
    _is_animation = False # Reset animation flag
    
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
    global _render_start_time, _email_sent, _render_in_progress, _is_animation
    
    # Reset state for new render
    _render_start_time = time.time()
    _email_sent = False
    _render_in_progress = True
    _is_animation = scene.render.engine != 'BLENDER_RENDER' and scene.render.use_sequencer is False # Check if it's animation
    print(f"⏱️ Render started - timer reset. Animation: {_is_animation}")

@persistent
def on_render_complete(scene=None, *args):  # Accept extra arguments for flexibility
    """Handler for render completion"""
    global _render_in_progress, _is_animation
    
    if not _render_in_progress:
        return
    # In render animtion case
    if _is_animation and scene.frame_current < scene.frame_end:
        print(f"🎬 Frame {scene.frame_current} of {_is_animation} complete - waiting for the rest")
        return # Wait for all frames
        
    print("✅ Render complete - scheduling email")
    # Schedule email with small delay to ensure everything is ready
    bpy.app.timers.register(send_render_notification_later, first_interval=0.5)

@persistent
def on_render_cancel(scene):
    """Handler for render cancellation/error"""
    global _email_sent, _render_in_progress, _is_animation
    
    if _email_sent or not _render_in_progress:
        return
        
    _email_sent = True
    _render_in_progress = False
    _is_animation = False
    print("⚠️ Render cancelled - sending notification")
    send_email("⚠️ Blender Render Cancelled", "The render was cancelled or encountered an error.")

def register_handlers():
    """Register our handlers with Blender"""
    print("🔄 Registering render notification handlers")
    
    # Remove any existing handlers first to prevent duplicates
    unregister_handlers()
    
    # Add our persistent handlers
    bpy.app.handlers.render_init.append(on_render_start)
    bpy.app.handlers.render_complete.append(on_render_complete)
    bpy.app.handlers.render_cancel.append(on_render_cancel)
    
    print("🔔 Registered render notification handlers")

def unregister_handlers():
    """Clean up all our handlers"""
    print("🔄 Unregistering render notification handlers")
    
    handlers = [
        (bpy.app.handlers.render_init, on_render_start),
        (bpy.app.handlers.render_complete, on_render_complete),
        (bpy.app.handlers.render_cancel, on_render_cancel)
    ]
    
    for handler_list, func in handlers:
        if func in handler_list:
            handler_list.remove(func)
            print(f"🗑️ Removed handler: {func.__name__}")
    
    # Clear any pending timers
    if hasattr(bpy.app, 'timers') and callable(getattr(bpy.app.timers, 'unregister', None)):
        try:
            bpy.app.timers.unregister(send_render_notification_later)
            print("🗑️ Unregistered timer")
        except:
            pass  # Timer might not be registered
    
    print("🔕 Unregistered render notification handlers")