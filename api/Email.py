from django.core.mail import EmailMessage
from .choices import RECIPIENTS

def create_mail(EventName,EventDate):
    #put the subject here
    subject = "Event report for {}".format(EventName)
    body = "Here is the report for the event {} on {}".format(EventName, EventDate)
    to = RECIPIENTS
    
    email = EmailMessage(
        subject=subject,
        body=body,
        to=to
    )
    return email

def send_mail(filename):
    #split the event name and the date by the separator introduced
    eventDetail_list = filename.split('$')
    EventName = eventDetail_list[0]
    #use the date only and not the extension eg. '.pdf, .txt, etc.'
    EventDate = eventDetail_list[1].split('.')[0]
    #get the email object
    email = create_mail(EventName,EventDate)
    #change the file path to media directory 
    file_path = 'media/' + filename
    #attach the file to the email
    email.attach_file(file_path)
    email.send()


