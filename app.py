from flask import Flask, request, jsonify, render_template
import os
import datetime
import uuid
import main

app = Flask(__name__)

# path to upload files
UPLOAD_FOLDER = 'UPLOAD_FOLDER/'

# route to uploading pdf file
@app.route('/file/upload', methods=['POST'])
def index():
    
    if request.method == 'POST':

        # saving current timestamp
        current_time = str(datetime.datetime.now()).replace('-', '_').replace(':', '_')
        ID = uuid.uuid4().hex
        # setting filename that is being received to current time stamp with its directory
        filename = UPLOAD_FOLDER + ID + '/' + current_time + '.pdf'

        # if the uuid folder doesn't already exist, create it
        if not os.path.exists(UPLOAD_FOLDER + ID):
            os.mkdir(UPLOAD_FOLDER + ID)
        
        # get pdf file
        photo = request.files['document']
        photo.save(filename)

        print("FILENAME: ", filename)
        result = main.main(filename)

        return(jsonify(result))


# GET
@app.route('/')
@app.route('/index')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run()
