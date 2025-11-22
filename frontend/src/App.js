import React, { useState } from "react";

function App() {
  const [place, setPlace] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const getTourismInfo = async () => {
    if (!place.trim()) {
      setError("Please enter a place name");
      return;
    }

    setLoading(true);
    setError("");
    setResponse("");

    try {
      const res = await fetch("http://127.0.0.1:5000/tourism", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ place: place.trim() }),
      });

      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`);
      }

      const data = await res.json();
      setResponse(data.answer);
    } catch (err) {
      setError("Failed to get response. Make sure the backend server is running.");
      console.error("Error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      getTourismInfo();
    }
  };

  const clearAll = () => {
    setPlace("");
    setResponse("");
    setError("");
  };

  return (
    <div style={{ 
      padding: "40px", 
      fontFamily: "Arial, sans-serif",
      maxWidth: "800px",
      margin: "0 auto",
      backgroundColor: "#f5f5f5",
      minHeight: "100vh"
    }}>
      <h1 style={{ 
        color: "#2c3e50", 
        textAlign: "center",
        marginBottom: "30px"
      }}>
        Tourism Multi-Agent Planner
      </h1>

      <div style={{ 
        backgroundColor: "white", 
        padding: "30px", 
        borderRadius: "10px",
        boxShadow: "0 2px 10px rgba(0,0,0,0.1)"
      }}>
        <div style={{ display: "flex", gap: "10px", marginBottom: "20px" }}>
          <input
            type="text"
            placeholder="Enter a place (e.g., 'I'm going to go to Bangalore, what is the temperature there')"
            value={place}
            onChange={(e) => {
              setPlace(e.target.value);
              setError("");
            }}
            onKeyPress={handleKeyPress}
            style={{ 
              flex: 1, 
              padding: "12px", 
              border: "1px solid #ddd",
              borderRadius: "5px",
              fontSize: "16px"
            }}
            disabled={loading}
          />

          <button
            onClick={getTourismInfo}
            disabled={loading || !place.trim()}
            style={{ 
              padding: "12px 24px", 
              backgroundColor: "#3498db",
              color: "white",
              border: "none",
              borderRadius: "5px",
              cursor: "pointer",
              fontSize: "16px",
              opacity: (loading || !place.trim()) ? 0.6 : 1
            }}
          >
            {loading ? "Loading..." : "Submit"}
          </button>

          <button
            onClick={clearAll}
            style={{ 
              padding: "12px 24px", 
              backgroundColor: "#e74c3c",
              color: "white",
              border: "none",
              borderRadius: "5px",
              cursor: "pointer",
              fontSize: "16px"
            }}
          >
            Clear
          </button>
        </div>

        {error && (
          <div style={{ 
            color: "#e74c3c", 
            padding: "10px", 
            backgroundColor: "#fadbd8",
            borderRadius: "5px",
            marginBottom: "20px"
          }}>
            {error}
          </div>
        )}

        {response && (
          <div style={{ 
            marginTop: "20px", 
            whiteSpace: "pre-line",
            padding: "20px",
            backgroundColor: "#e8f4f8",
            borderRadius: "5px",
            border: "1px solid #3498db"
          }}>
            <h3 style={{ color: "#2c3e50", marginTop: 0 }}>Response:</h3>
            <div style={{ fontSize: "16px", lineHeight: "1.6" }}>
              {response}
            </div>
          </div>
        )}

        {!response && !error && !loading && (
          <div style={{ 
            textAlign: "center", 
            color: "#7f8c8d", 
            marginTop: "40px",
            fontStyle: "italic"
          }}>
            <p>Try asking about any place in the world!</p>
            <p>Examples:</p>
            <ul style={{ listStyle: "none", padding: 0 }}>
              <li>"I'm going to go to Bangalore, what is the temperature there"</li>
              <li>"What places can I visit in Paris?"</li>
              <li>"I'm planning a trip to Tokyo"</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;