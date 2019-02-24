import pickle
import random
import string
import validators
#from imgurpython import ImgurClient
from flask import Flask, flash, render_template, redirect, request, url_for
from pymessenger.bot import Bot
from bs4 import BeautifulSoup
import requests
import re
from bs4 import BeautifulSoup as Soup
from html.parser import HTMLParser

class MyParser(HTMLParser):
    def __init__(self, output_list=None):
        HTMLParser.__init__(self)
        if output_list is None:
            self.output_list = []
        else:
            self.output_list = output_list
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.output_list.append(dict(attrs).get('href'))



URL_regex = '[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)'
URL_pattern = re.compile(URL_regex)
app = Flask(__name__)
app.secret_key = 'MAKE_THIS_VERY_HARD_TO_GUESS'


ACCESS_TOKEN = 'EAAEiLjL0GxoBALzavZAXkNIav6sc5t9PptOxNve1HDgpLRZAmIZBanvgoaXBJC8s6ZAdlYyvq4vI0zgNqtm62fxKSZCCMCpamQtUAG8YWRsccBhoTFLufFkN8xRDuDxvJHhj08I3s6pZCGXT9XYsLS42p98t1U8ZBEYZA2EG4gtKvVtsQjuXEtM5'
VERIFY_TOKEN = 'VERIFY_TOKEN'
bot = Bot(ACCESS_TOKEN)




# index route
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = str(request.form.get('url'))  # get url from POSTed form data

        with open('url_list.p') as f:
            url_list = pickle.load(f)  # list of (url, hash) tuples

        # Handle POSTed URLs that have been shortened previously
        for item in url_list:
            if url == item[0]:
                shortened_url = 'https://c-om.press/%s' % item[1]
                return redirect(url_for('shortened', url=shortened_url))

        # handle new URLs to be shortened
        letters = string.ascii_letters + string.digits  # a-Z + 0-9
        # create random hash of 7 chars length from letters
        url_hash = ''.join(random.SystemRandom().choice(letters) for n in range(7))
        # add new URL and associated hash to url_list as tuple
        url_list.append((url, url_hash))

        # repickle url_list
        with open('url_list.p', 'w') as f:
            pickle.dump(url_list, f)

        # redirect to shortened page displaying shortened URL
        # shortened URL passed as query param
        shortened_url = 'https://c-om.press/%s' % url_hash
        return redirect(url_for('shortened', url=shortened_url))

    else:
        # get request, renders form for submitting url to shorten
        return render_template('index.html')


# route for shortened url display page
@app.route('/shortened/')
def shortened():
    url = request.args.get('url')
    return render_template('shortened.html', url=url)


# route for redirect shortened urls to full url
@app.route('/<hash>/')
def redirect_url(hash):
    with open('url_list.p') as f:
        url_list = pickle.load(f)
    for item in url_list:
        if hash == item[1]:
            return redirect(item[0])
    flash("<strong>Redirect failed:</strong> shortened url does not exist. Enter a url to shorten below.")
    return redirect(url_for('index'))


#We will receive messages that Facebook sends our bot at this endpoint 
@app.route("/bot", methods=['GET', 'POST'])
def receive_message():
    if request.method == 'GET':
        """Before allowing people to message your bot, Facebook has implemented a verify token
        that confirms all requests that your bot receives came from Facebook.""" 
        token_sent = request.args.get("hub.verify_token")
        return verify_fb_token(token_sent)
    #if the request was not get, it must be POST and we can just proceed with sending a message back to user
    else:
        # get whatever message a user sent the bot
        output = request.get_json()
        for event in output['entry']:
          messaging = event['messaging']
          for message in messaging:
            if message.get('message'):
                #print(message['message'].get('text'))

                if message['message'].get('text'):
                    if(1):
                        text = message['message'].get('text')
                        print(text)
                        recipient_id = message['sender']['id']
                        #send_message(recipient_id, getNetID(text))
                        p = MyParser()
                        p.feed(text)
                        matches = p.output_list
                        #matches = re.findall(URL_pattern, text);
                        #for url in matches:
                        if(validators.url(text)):
                        #if(URL_pattern.match(text)):
                            print("LINK")
                            url = text
                            with open('url_list.p', 'rb') as f:
                                url_list = pickle.load(f)  # list of (url, hash) tuples

                            # Handle POSTed URLs that have been shortened previously
                            for item in url_list:
                                if url == item[0]:
                                    shortened_url = 'https://c-om.press/%s' % item[1]
                                    return redirect(url_for('shortened', url=shortened_url))

                            # handle new URLs to be shortened
                            letters = string.ascii_letters + string.digits  # a-Z + 0-9
                            # create random hash of 7 chars length from letters
                            url_hash = ''.join(random.SystemRandom().choice(letters) for n in range(7))
                            # add new URL and associated hash to url_list as tuple
                            url_list.append((url, url_hash))

                            # repickle url_list
                            with open('url_list.p', 'wb') as f:
                                pickle.dump(url_list, f)

                            # redirect to shortened page displaying shortened URL
                            # shortened URL passed as query param
                            shortened_url = 'https://c-om.press/%s' % url_hash
                            print(shortened_url)

                            recipient_id = message['sender']['id']
                            print(message )
                            response_sent_text = "Original URL: " + url +  "\nShortened URL: " + shortened_url
                            send_message(recipient_id, response_sent_text)
                
                #Facebook Messenger ID for user so we know where to send response back to
                recipient_id = message['sender']['id']
                if message['message'].get('text'):
                    response_sent_text = get_message()
                    #send_message(recipient_id, response_sent_text)
                #if user sends us a GIF, photo,video, or any other non-text item
                if message['message'].get('attachments'):
                    response_sent_nontext = get_message()
                    send_message(recipient_id, response_sent_nontext)
    return "Message Processed"


def verify_fb_token(token_sent):
    #take token sent by facebook and verify it matches the verify token you sent
    #if they match, allow the request, else return an error 
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'


#chooses a random message to send to the user
def get_message():
    sample_responses = ["That's a nice attachment but I can only shorten URLs. :("]
    # return selected item to the user
    return random.choice(sample_responses)

#uses PyMessenger to send response to user
def send_message(recipient_id, response):
    #sends user the text message provided via input response parameter
    bot.send_text_message(recipient_id, response)
    return "success"


if __name__ == '__main__':
    app.run(debug=True)
