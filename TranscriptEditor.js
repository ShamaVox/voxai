import React, { useRef, useState, useEffect } from 'react';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import axios from 'axios';

const TranscriptEditor = () => {
  const [candidateId, setCandidateId] = useState('');
  const [content, setContent] = useState('');
  const [summary, setSummary] = useState('');
  const [highlighted, setHighlighted] = useState('');
  const quillRef = useRef(null);
  const [timer, setTimer] = useState(null);

  // API config
  const API_KEY = 'your-api-key';
  const BASE_URL = 'http://localhost:5000';

  /**
   * npm install react-quill axios
   * How this script works:
   * 1. Enter candidate ID
   * 2. Paste or type interview transcript into Quill editor
   * 3. Click Save & Generate Summary
   * 4. Sends HTML + Delta to Flask API
   * 5. Receives & displays AI-generated summary
   * 6. Highlights keywords using AI (optional)
   * 7. Autosaves after 3 seconds of inactivity
   */

  // Save notes and get AI summary
  const handleSave = async () => {
    if (!candidateId) {
      alert('Please enter a candidate ID.');
      return;
    }

    const html = quillRef.current.getEditor().root.innerHTML;
    const delta = quillRef.current.getEditor().getContents();

    try {
      const res = await axios.post(
        `${BASE_URL}/notes`,
        { candidateId, notes: html, delta },
        {
          headers: {
            'x-api-key': API_KEY,
            'Content-Type': 'application/json',
          },
        }
      );

      setSummary(res.data.summary || '');
      highlightImportantPhrases(res.data.summary);
    } catch (err) {
      console.error(err);
      alert('Error saving notes.');
    }
  };

  // Retrieve saved notes
  const handleFetch = async () => {
    try {
      const res = await axios.get(`${BASE_URL}/notes/${candidateId}`, {
        headers: { 'x-api-key': API_KEY },
      });

      setContent(res.data.notes_html);
      setSummary(res.data.summary);
      highlightImportantPhrases(res.data.summary);
    } catch (err) {
      console.error(err);
      alert('No notes found.');
    }
  };

  // Highlight keywords in editor using summary
  const highlightImportantPhrases = (summaryText) => {
    const words = summaryText
      .split(' ')
      .filter((w) => w.length > 5)
      .slice(0, 5); // Take top 5 keywords

    const editor = quillRef.current.getEditor();
    const text = editor.getText();
    words.forEach((word) => {
      let start = 0;
      while (start !== -1) {
        start = text.indexOf(word, start);
        if (start !== -1) {
          editor.formatText(start, word.length, { background: '#ffe58f' });
          start += word.length;
        }
      }
    });

    setHighlighted(words.join(', '));
  };

  // Autosave every 3s after typing stops
  const handleChange = (value) => {
    setContent(value);
    if (timer) clearTimeout(timer);
    setTimer(setTimeout(() => handleSave(), 3000));
  };

  // Quill modules
  const modules = {
    toolbar: [
      [{ header: [1, 2, false] }],
      ['bold', 'italic', 'underline'],
      ['link'],
      [{ list: 'ordered' }, { list: 'bullet' }],
      ['clean'],
    ],
  };

  return (
    <div style={{ maxWidth: '800px', margin: '2rem auto' }}>
      <h2>VoxAI: Interview Transcript Editor</h2>

      <input
        type="text"
        placeholder="Enter Candidate ID"
        value={candidateId}
        onChange={(e) => setCandidateId(e.target.value)}
        style={{ width: '100%', padding: '10px', marginBottom: '1rem' }}
      />

      <ReactQuill
        ref={quillRef}
        theme="snow"
        value={content}
        onChange={handleChange}
        modules={modules}
      />

      <div style={{ marginTop: '1rem' }}>
        <button onClick={handleSave} style={{ marginRight: '10px' }}>
          Save & Generate Summary
        </button>
        <button onClick={handleFetch}>Fetch Notes</button>
      </div>

      {summary && (
        <div style={{ marginTop: '2rem', padding: '1rem', backgroundColor: '#f9f9f9' }}>
          <h3>🧠 AI Summary</h3>
          <p>{summary}</p>
          {highlighted && (
            <div>
              <small><strong>Highlighted Phrases:</strong> {highlighted}</small>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TranscriptEditor;
