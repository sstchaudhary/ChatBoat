import { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadDocument } from '../api/api';

export default function FileUpload({ onUploadSuccess }) {
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');

  const onDrop = async (acceptedFiles) => {
    if (!acceptedFiles.length) {
      setMessage('No file selected.');
      return;
    }

    setUploading(true);
    setMessage('');
    const file = acceptedFiles[0];

    try {
      const res = await uploadDocument(file);
      setMessage(
        res.data.warning
          ? `Upload complete, but indexing failed: ${res.data.warning}`
          : `✓ ${res.data.message}`
      );
      onUploadSuccess();
    } catch (err) {
      setMessage(err.response?.data?.error || 'Upload failed.');
    } finally {
      setUploading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
  });

  return (
    <div className="upload-section">
      <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
        <input {...getInputProps()} />
        {uploading ? (
          <p>Uploading…</p>
        ) : (
          <p>{isDragActive ? 'Drop the file here...' : 'Drag & drop PDF, DOCX, or TXT here, or click to select.'}</p>
        )}
      </div>
      {message && <p className="upload-message">{message}</p>}
    </div>
  );
}
