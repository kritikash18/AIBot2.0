from flask import Flask, redirect, url_for, render_template, request, jsonify
from functions import process_document, query_response, moderation_check, query_response_enhanced
from datetime import datetime
import threading
import traceback

app = Flask(__name__)
app.secret_key = '12345'

global pdf_path
pdf_path = "data"

documents_ready = False
def process_documents_background(pdf_path):
    global processed_documents, documents_ready
#     processed_documents = process_document(pdf_path, True)
    processed_documents = process_document(pdf_path)
    documents_ready = True


@app.route('/')
def default_func():
    threading.Thread(target=process_documents_background, args=(pdf_path,)).start()
    conversation_bot = [{"bot": "Hello, This is Insurance Helpmate. Please wait while I equip myself to answer questions related to Principal Insurance Policy. \n Processing..."}]
    now = datetime.now()
    user_time = now.strftime("%H:%M")
    return render_template("chat.html", name_xyz = conversation_bot, user_time = user_time)

@app.route('/check-processing')
def check_processing():
    try:
        if documents_ready:
            return jsonify({'status': 'completed'})
        else:
            return jsonify({'status': 'processing'})
    except Exception as e:
        print(f"Error in check-processing: {e}") 
        return jsonify({'error': 'An error occurred'}), 500

@app.route("/end_conv", methods = ['POST'])
def end_conv():
    return redirect(url_for('default_func'))

@app.route("/getresponse", methods = ['POST'])
def getresponse():
    global processed_documents
    user_input = request.form["user_input_message"]
    moderation = moderation_check(user_input)
    if moderation == 'Flagged':
        return jsonify({"message": "Sorry, this message has been flagged. Cannot proceed further."})
    try:
#         response = query_response(user_input, processed_documents)
        response = query_response_enhanced(user_input, processed_documents)
        return jsonify({"message": response})
    except Exception as e:
        app.logger.error(f"An unexpected error occurred: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "An unexpected error occurred"}), 500




if __name__ == '__main__':
    app.run(debug=True) 