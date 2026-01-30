import { useEffect, useRef, useState } from "react";

export function useVoiceInput({ onResult, onEnd }) {
  const recognitionRef = useRef(null);
  const [supported, setSupported] = useState(true);
  const [listening, setListening] = useState(false);

  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onstart = () => setListening(true);

    recognition.onend = () => {
      setListening(false);
      onEnd?.();
    };

    recognition.onresult = (event) => {
      let transcript = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      onResult(transcript);
    };

    recognitionRef.current = recognition;
  }, [onResult, onEnd]);

  const start = () => {
    if (!recognitionRef.current) return;
    recognitionRef.current.start();
  };

  const stop = () => {
    recognitionRef.current?.stop();
  };

  return {
    supported,
    listening,
    start,
    stop,
  };
}
