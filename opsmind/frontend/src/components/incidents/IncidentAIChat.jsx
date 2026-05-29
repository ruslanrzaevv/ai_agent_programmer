// src/components/incidents/IncidentAIChat.jsx

import {
    useState,
  } from "react";
  
  import {
    askAI,
  } from "../../api/incidentApi";
  
  export default function IncidentAIChat({
    incidentId,
  }) {
  
    const [
      question,
      setQuestion,
    ] = useState("");
  
    const [
      answer,
      setAnswer,
    ] = useState("");
  
    async function send() {
  
      const response =
        await askAI(
          incidentId,
          question
        );
  
      setAnswer(
        response.data.answer
      );
    }
  
    return (
  
      <div>
  
        <h3>
          AI Assistant
        </h3>
  
        <input
          value={
            question
          }
          onChange={(e) =>
            setQuestion(
              e.target.value
            )
          }
        />
  
        <button
          onClick={send}
        >
          Ask
        </button>
  
        {answer && (
          <div>
            {answer}
          </div>
        )}
  
      </div>
  
    );
  }