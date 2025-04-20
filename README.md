# Render-Email-Notifier-Blender
The add-on that automatically sends email notifications when a render process is completed, and sends warning if render error. With this tool, you can comfortably away from keyboard, and receive emails containing render results right after the process finishes, saving you time and providing convenience in 3D content production.


KEY FEATURES:

Auto Email Notification: Sends an email right after rendering is finished.

Render Info Included: Details like engine, resolution, frame, samples, and render time are included in the email.

Multiple Recipients: Add a list of recipient emails or choose to send only to yourself.

Send Test Email: Verify your setup before running actual renders.

Error Alerts: Get notified if the render is canceled or fails.

![Render-email-notifier-preivew](https://github.com/user-attachments/assets/7332817a-8da5-4b94-a511-a9048cadfdd0)



📘 HOW TO USE

Install the Add-on

Download zip add-on folder.
In Blender, go to Edit > Preferences > Add-ons > Install... and select the file.
Go to the Render Properties tab > "Render Mail Notifier Settings".

Fill in:
Sender Email: Your Gmail address.
Password: Your App Password.
Recipients: Add one or more recipient emails, or enable “Send Myself”.

RUN a Render. After completion, the add-on will automatically send an email with the render details and preview image.

(Optional) Click the "Send Test Email" button to make sure everything is working.


  
🔐 HOW TO GET GMAIL APP PASSWORD

To allow the add-on to send emails securely from your Gmail account, you need to generate an App Password. Here’s how:

Step-by-Step:
Enable 2-Step Verification for your Google account:
https://myaccount.google.com/security > Sign in to Google > Turn on 2-Step Verification.

After enabling 2-Step Verification, go to:
https://myaccount.google.com/apppasswords

Select:
App: Choose "Other (Custom name)" and type Blender Notifier.
Device: You can leave the default.
Click Generate.
Google will give you a 16-character password (e.g., abcd efgh ijkl mnop).
Copy this password and paste it into the Password field in the add-on.

🛡️ Note: This password is different from your normal Google password and is only used by apps like this one. Keep it private.
