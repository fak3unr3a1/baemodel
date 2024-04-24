# from flask import Flask, render_template, request, jsonify
# import speech_recognition as sr
# from gtts import gTTS
# import os

# app = Flask(__name__)

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/speech_to_text', methods=['POST'])
# def speech_to_text():
#     # Check if the 'audio' file is included in the request
#     if 'audio' not in request.files:
#         return jsonify({'error': 'No audio file provided'})

#     audio_file = request.files['audio']
    
#     # Save the audio file temporarily
#     audio_path = 'temp_audio.wav'
#     audio_file.save(audio_path)

#     # Use SpeechRecognition library to convert speech to text
#     recognizer = sr.Recognizer()
#     with sr.AudioFile(audio_path) as source:
#         audio_data = recognizer.record(source)

#     try:
#         text = recognizer.recognize_google(audio_data)
#         os.remove(audio_path)  # Delete the temporary audio file
#         return jsonify({'text': text})
#     except sr.UnknownValueError:
#         return jsonify({'error': 'Speech recognition could not understand audio'})
#     except sr.RequestError as e:
#         return jsonify({'error': f'Speech recognition service error: {str(e)}'})

# @app.route('/text_to_speech', methods=['POST'])
# def text_to_speech():
#     text = request.form.get('text')
#     if not text:
#         return jsonify({'error': 'No text provided'})

#     # Use gTTS library to convert text to speech
#     tts = gTTS(text)
#     tts.save('output_audio.mp3')

#     return jsonify({'message': 'Text converted to speech successfully'})

# if __name__ == '__main__':
#     app.run(debug=True)
# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Speech to Text and Text to Speech</title>
# </head>
# <body>
#     <h1>Speech to Text and Text to Speech</h1>

#     <h2>Speech to Text</h2>
#     <form id="speechToTextForm" enctype="multipart/form-data">
#         <input type="file" id="audioInput" name="audio" accept="audio/*" required>
#         <button type="submit">Convert Speech to Text</button>
#     </form>
#     <div id="speechToTextResult"></div>

#     <h2>Text to Speech</h2>
#     <form id="textToSpeechForm">
#         <textarea id="textInput" name="text" placeholder="Enter text here" required></textarea>
#         <button type="submit">Convert Text to Speech</button>
#     </form>
#     <div id="textToSpeechResult"></div>

#     <script>
#         document.getElementById('speechToTextForm').onsubmit = function(event) {
#             event.preventDefault(); // Prevent form submission
#             var formData = new FormData(this); // Create FormData object
#             fetch('/speech_to_text', {
#                 method: 'POST',
#                 body: formData
#             })
#             .then(response => response.json())
#             .then(data => {
#                 if (data.text) {
#                     document.getElementById('speechToTextResult').innerHTML = '<p>Text: ' + data.text + '</p>';
#                 } else if (data.error) {
#                     document.getElementById('speechToTextResult').innerHTML = '<p>Error: ' + data.error + '</p>';
#                 }
#             })
#             .catch(error => {
#                 console.error('Error:', error);
#             });
#         };

#         document.getElementById('textToSpeechForm').onsubmit = function(event) {
#             event.preventDefault(); // Prevent form submission
#             var text = document.getElementById('textInput').value;
#             fetch('/text_to_speech', {
#                 method: 'POST',
#                 headers: {
#                     'Content-Type': 'application/json'
#                 },
#                 body: JSON.stringify({text: text})
#             })
#             .then(response => response.json())
#             .then(data => {
#                 if (data.message) {
#                     document.getElementById('textToSpeechResult').innerHTML = '<p>Text converted to speech successfully. <a href="/output_audio.mp3" download>Download audio</a></p>';
#                 } else if (data.error) {
#                     document.getElementById('textToSpeechResult').innerHTML = '<p>Error: ' + data.error + '</p>';
#                 }
#             })
#             .catch(error => {
#                 console.error('Error:', error);
#             });
#         };
#     </script>
# </body>
# </html>
