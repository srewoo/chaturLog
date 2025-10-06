import React, { useState, useRef } from 'react';
import { Upload, X, CheckCircle, AlertCircle, FileText } from 'lucide-react';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { cn } from '../lib/utils';

/**
 * Enhanced File Upload Component with drag-and-drop, validation, and progress tracking
 * 
 * @param {Object} props
 * @param {Function} props.onFileSelect - Callback when file is selected
 * @param {Function} props.onFileRemove - Callback when file is removed
 * @param {Array} props.acceptedTypes - Array of accepted file extensions (e.g., ['.log', '.txt'])
 * @param {Number} props.maxSizeMB - Maximum file size in MB
 * @param {String} props.className - Additional CSS classes
 */
export default function FileUpload({ 
  onFileSelect, 
  onFileRemove,
  acceptedTypes = ['.log', '.txt', '.json'],
  maxSizeMB = 50,
  className 
}) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef(null);

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const validateFile = (file) => {
    setError('');

    // Check file type
    const extension = '.' + file.name.split('.').pop().toLowerCase();
    if (!acceptedTypes.includes(extension)) {
      setError(`Invalid file type. Accepted: ${acceptedTypes.join(', ')}`);
      return false;
    }

    // Check file size
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > maxSizeMB) {
      setError(`File too large. Maximum size: ${maxSizeMB}MB`);
      return false;
    }

    return true;
  };

  const handleFileSelect = (file) => {
    if (validateFile(file)) {
      setSelectedFile(file);
      setUploadProgress(0);
      
      // Simulate upload progress (replace with actual upload logic if needed)
      const interval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 100) {
            clearInterval(interval);
            return 100;
          }
          return prev + 10;
        });
      }, 100);

      if (onFileSelect) {
        onFileSelect(file);
      }
    }
  };

  const handleFileRemove = () => {
    setSelectedFile(null);
    setError('');
    setUploadProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    if (onFileRemove) {
      onFileRemove();
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  return (
    <div className={cn('w-full', className)}>
      {/* Upload Area */}
      {!selectedFile ? (
        <div
          className={cn(
            'relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200',
            dragActive 
              ? 'border-blue-500 bg-blue-50' 
              : 'border-slate-300 hover:border-slate-400 bg-slate-50'
          )}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          data-testid="file-upload-dropzone"
        >
          <Upload className={cn(
            'h-12 w-12 mx-auto mb-4 transition-colors',
            dragActive ? 'text-blue-500' : 'text-slate-400'
          )} />
          
          <div className="space-y-2">
            <p className="text-lg font-medium text-slate-700">
              {dragActive ? 'Drop your file here' : 'Drag & drop your log file'}
            </p>
            <p className="text-sm text-slate-500">
              or click to browse
            </p>
            <p className="text-xs text-slate-400 mt-2">
              Supported: {acceptedTypes.join(', ')} • Max {maxSizeMB}MB
            </p>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            onChange={handleChange}
            accept={acceptedTypes.join(',')}
            className="hidden"
            id="file-input"
            data-testid="file-input"
          />
          
          <label htmlFor="file-input" className="mt-4 inline-block">
            <Button 
              type="button"
              variant="outline" 
              className="cursor-pointer"
              onClick={() => fileInputRef.current?.click()}
              data-testid="browse-button"
            >
              Browse Files
            </Button>
          </label>
        </div>
      ) : (
        /* Selected File Display */
        <div 
          className="border border-slate-200 rounded-lg p-6 bg-white"
          data-testid="selected-file-display"
        >
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-start space-x-3 flex-1">
              <FileText className="h-10 w-10 text-blue-500 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-900 truncate">
                  {selectedFile.name}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  {formatFileSize(selectedFile.size)}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleFileRemove}
              className="flex-shrink-0"
              data-testid="remove-file-button"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Upload Progress */}
          {uploadProgress < 100 ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-600">
                <span>Uploading...</span>
                <span>{uploadProgress}%</span>
              </div>
              <Progress value={uploadProgress} className="h-2" />
            </div>
          ) : (
            <div className="flex items-center space-x-2 text-sm text-green-600">
              <CheckCircle className="h-4 w-4" />
              <span>File ready for analysis</span>
            </div>
          )}
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div 
          className="mt-4 flex items-start space-x-2 p-3 bg-red-50 border border-red-200 rounded-lg"
          data-testid="error-message"
        >
          <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}
    </div>
  );
}

