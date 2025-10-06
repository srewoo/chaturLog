/**
 * File Validation Utilities
 * Provides validation functions for file uploads
 */

/**
 * Allowed file types for log analysis
 */
export const ALLOWED_FILE_TYPES = {
  LOG: '.log',
  TXT: '.txt',
  JSON: '.json'
};

/**
 * Default maximum file size in MB
 */
export const DEFAULT_MAX_FILE_SIZE_MB = 50;

/**
 * Get file extension from filename
 * @param {string} filename - The name of the file
 * @returns {string} The file extension (including dot)
 */
export const getFileExtension = (filename) => {
  if (!filename || typeof filename !== 'string') {
    return '';
  }
  const parts = filename.split('.');
  return parts.length > 1 ? `.${parts.pop().toLowerCase()}` : '';
};

/**
 * Check if file type is allowed
 * @param {string} filename - The name of the file
 * @param {Array<string>} allowedTypes - Array of allowed extensions (e.g., ['.log', '.txt'])
 * @returns {boolean} True if file type is allowed
 */
export const isFileTypeAllowed = (filename, allowedTypes = Object.values(ALLOWED_FILE_TYPES)) => {
  const extension = getFileExtension(filename);
  return allowedTypes.includes(extension);
};

/**
 * Check if file size is within limit
 * @param {number} fileSizeBytes - File size in bytes
 * @param {number} maxSizeMB - Maximum allowed size in MB
 * @returns {boolean} True if file size is acceptable
 */
export const isFileSizeValid = (fileSizeBytes, maxSizeMB = DEFAULT_MAX_FILE_SIZE_MB) => {
  const fileSizeMB = fileSizeBytes / (1024 * 1024);
  return fileSizeMB <= maxSizeMB;
};

/**
 * Format file size to human-readable string
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size (e.g., "1.5 MB")
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return `${Math.round((bytes / Math.pow(k, i)) * 100) / 100} ${sizes[i]}`;
};

/**
 * Validate a file object
 * @param {File} file - The file object to validate
 * @param {Object} options - Validation options
 * @param {Array<string>} options.allowedTypes - Allowed file extensions
 * @param {number} options.maxSizeMB - Maximum file size in MB
 * @returns {Object} Validation result with isValid and error message
 */
export const validateFile = (file, options = {}) => {
  const {
    allowedTypes = Object.values(ALLOWED_FILE_TYPES),
    maxSizeMB = DEFAULT_MAX_FILE_SIZE_MB
  } = options;

  // Check if file exists
  if (!file) {
    return {
      isValid: false,
      error: 'No file selected'
    };
  }

  // Check file type
  if (!isFileTypeAllowed(file.name, allowedTypes)) {
    return {
      isValid: false,
      error: `Invalid file type. Allowed types: ${allowedTypes.join(', ')}`
    };
  }

  // Check file size
  if (!isFileSizeValid(file.size, maxSizeMB)) {
    return {
      isValid: false,
      error: `File too large. Maximum size: ${maxSizeMB}MB (Current: ${formatFileSize(file.size)})`
    };
  }

  // Check if file name is too long
  if (file.name.length > 255) {
    return {
      isValid: false,
      error: 'File name is too long (maximum 255 characters)'
    };
  }

  // Additional security check for dangerous characters in filename
  const dangerousChars = /[<>:"|?*\x00-\x1f]/;
  if (dangerousChars.test(file.name)) {
    return {
      isValid: false,
      error: 'File name contains invalid characters'
    };
  }

  return {
    isValid: true,
    error: null
  };
};

/**
 * Read file content as text
 * @param {File} file - The file to read
 * @returns {Promise<string>} Promise that resolves with file content
 */
export const readFileAsText = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (e) => {
      resolve(e.target.result);
    };
    
    reader.onerror = (e) => {
      reject(new Error('Failed to read file'));
    };
    
    reader.readAsText(file);
  });
};

/**
 * Get file metadata
 * @param {File} file - The file object
 * @returns {Object} File metadata
 */
export const getFileMetadata = (file) => {
  if (!file) return null;
  
  return {
    name: file.name,
    size: file.size,
    sizeFormatted: formatFileSize(file.size),
    type: file.type || 'unknown',
    extension: getFileExtension(file.name),
    lastModified: file.lastModified,
    lastModifiedDate: new Date(file.lastModified)
  };
};

/**
 * Check if file is empty
 * @param {File} file - The file object
 * @returns {boolean} True if file is empty
 */
export const isFileEmpty = (file) => {
  return file && file.size === 0;
};

/**
 * Validate multiple files
 * @param {FileList|Array<File>} files - Files to validate
 * @param {Object} options - Validation options
 * @returns {Object} Validation results
 */
export const validateMultipleFiles = (files, options = {}) => {
  const results = {
    valid: [],
    invalid: [],
    totalSize: 0
  };

  Array.from(files).forEach(file => {
    const validation = validateFile(file, options);
    
    if (validation.isValid) {
      results.valid.push(file);
      results.totalSize += file.size;
    } else {
      results.invalid.push({
        file,
        error: validation.error
      });
    }
  });

  return results;
};

export default {
  ALLOWED_FILE_TYPES,
  DEFAULT_MAX_FILE_SIZE_MB,
  getFileExtension,
  isFileTypeAllowed,
  isFileSizeValid,
  formatFileSize,
  validateFile,
  readFileAsText,
  getFileMetadata,
  isFileEmpty,
  validateMultipleFiles
};

