import streamlit as st
import sounddevice as sd
import librosa
import numpy as np
import pandas as pd
import pickle
import os
from sklearn.neighbors import KNeighborsClassifier
 
def record_audio(duration=5, fs=44100):
    """Record audio for a given duration and return as numpy array."""
    st.info(f"Recording for {duration} seconds...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=2)
    sd.wait()
    st.success("Recording complete!")
    return audio
 
def extract_features(audio, sr=44100):
    """Extract MFCC features from the audio."""
    mfccs = librosa.feature.mfcc(y=audio[:, 0], sr=sr, n_mfcc=13)
    return np.mean(mfccs.T, axis=0)
 
def load_data_from_excel(file_path):
    data = pd.read_excel(file_path)
    labels = []
    features = []
    for index, row in data.iterrows():
        file_path = row['file_path']
        label = row['label']
        try:
            audio, sr = librosa.load(file_path, sr=None)
            mfccs = extract_features(audio, sr)
            features.append(mfccs)
            labels.append(label)
        except Exception as e:
            st.error(f"Error processing file {file_path}: {e}")
    return np.array(features), np.array(labels)
 
def train_model(file_path):
    features, labels = load_data_from_excel(file_path)
    if len(features) == 0 or len(labels) == 0:
        st.error("No data found. Please ensure your Excel file has valid entries.")
        return
    model = KNeighborsClassifier(n_neighbors=5)
    model.fit(features, labels)
    with open('knn_model.pkl', 'wb') as file:
        pickle.dump(model, file)
    st.success("Model trained and saved.")
 
def load_model(model_path='knn_model.pkl'):
    """Load the pre-trained model."""
    with open(model_path, 'rb') as file:
        model = pickle.load(file)
    return model
 
def main():
    st.title("Speaker Recognition App")
 
    excel_file_path = "C:/Users/vincent.koech/Desktop/Python/SondRecognition/voice_dataset.xlsx"
 
    if not os.path.exists('knn_model.pkl'):
        st.write("Training model, please wait...")
        train_model(excel_file_path)
        st.write("Model trained!")
 
    st.write("Press the button below to record audio.")
    if st.button("Record Audio"):
        audio = record_audio()
        features = extract_features(audio)
        model = load_model()
 
        prediction = model.predict([features.reshape(1, -1)])
        st.write(f"Predicted Speaker: {prediction[0]}")
 
if __name__ == "__main__":
    main()
 