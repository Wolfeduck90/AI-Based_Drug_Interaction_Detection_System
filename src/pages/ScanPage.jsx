import React, { useState, useRef } from 'react'
import { Camera, Upload, FileImage, Loader2, CheckCircle, AlertTriangle } from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import CameraCapture from '../components/CameraCapture'
import InteractionAlert from '../components/InteractionAlert'
import { useMedicationStore } from '../stores/medicationStore'
import toast from 'react-hot-toast'

const ScanPage = () => {
  const [showCamera, setShowCamera] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [scanResult, setScanResult] = useState(null)
  const [isScanning, setIsScanning] = useState(false)
  const fileInputRef = useRef(null)
  
  const { scanPrescription, addMedication } = useMedicationStore()

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.webp']
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setSelectedFile(acceptedFiles[0])
        setScanResult(null)
      }
    },
    onDropRejected: (rejectedFiles) => {
      const error = rejectedFiles[0]?.errors[0]
      if (error?.code === 'file-too-large') {
        toast.error('File too large. Please select an image under 10MB.')
      } else if (error?.code === 'file-invalid-type') {
        toast.error('Invalid file type. Please select an image file.')
      } else {
        toast.error('Failed to upload file. Please try again.')
      }
    }
  })

  const handleCameraCapture = (file) => {
    setSelectedFile(file)
    setShowCamera(false)
    setScanResult(null)
  }

  const handleFileSelect = (event) => {
    const file = event.target.files[0]
    if (file) {
      setSelectedFile(file)
      setScanResult(null)
    }
  }

  const handleScan = async () => {
    if (!selectedFile) {
      toast.error('Please select an image first')
      return
    }

    setIsScanning(true)
    
    try {
      const result = await scanPrescription(selectedFile)
      
      if (result.success) {
        setScanResult(result.data)
        toast.success('Prescription scanned successfully!')
      } else {
        toast.error(result.error || 'Failed to scan prescription')
      }
    } catch (error) {
      toast.error('An error occurred while scanning')
    } finally {
      setIsScanning(false)
    }
  }

  const handleAddMedication = async (medication) => {
    const result = await addMedication({
      name: medication.name,
      generic_name: medication.generic_name,
      dosage: medication.dosage,
      frequency: medication.frequency,
      prescriber: medication.prescriber,
      pharmacy: medication.pharmacy
    })

    if (result.success) {
      toast.success(`${medication.name} added to your medications`)
    } else {
      toast.error(result.error || 'Failed to add medication')
    }
  }

  const clearSelection = () => {
    setSelectedFile(null)
    setScanResult(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Scan Prescription
        </h1>
        <p className="text-gray-600">
          Take a photo or upload an image of your prescription label to detect potential drug interactions
        </p>
      </div>

      {!selectedFile && !scanResult && (
        <>
          {/* Upload options */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
            <button
              onClick={() => setShowCamera(true)}
              className="card hover:shadow-md transition-shadow text-center group"
            >
              <div className="w-16 h-16 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-4 group-hover:bg-primary-200 transition-colors">
                <Camera className="h-8 w-8 text-primary-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Take Photo</h3>
              <p className="text-sm text-gray-600">
                Use your camera to capture the prescription label
              </p>
            </button>

            <button
              onClick={() => fileInputRef.current?.click()}
              className="card hover:shadow-md transition-shadow text-center group"
            >
              <div className="w-16 h-16 bg-success-100 rounded-lg flex items-center justify-center mx-auto mb-4 group-hover:bg-success-200 transition-colors">
                <Upload className="h-8 w-8 text-success-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Upload Image</h3>
              <p className="text-sm text-gray-600">
                Select an image from your device
              </p>
            </button>
          </div>

          {/* Drag and drop area */}
          <div
            {...getRootProps()}
            className={`card border-2 border-dashed transition-colors cursor-pointer ${
              isDragActive
                ? 'border-primary-400 bg-primary-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <input {...getInputProps()} />
            <div className="text-center py-12">
              <FileImage className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-lg font-medium text-gray-900 mb-2">
                {isDragActive ? 'Drop the image here' : 'Drag and drop an image here'}
              </p>
              <p className="text-sm text-gray-600">
                or click anywhere to select a file
              </p>
              <p className="text-xs text-gray-500 mt-2">
                Supports JPEG, PNG, WebP (max 10MB)
              </p>
            </div>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            className="hidden"
          />
        </>
      )}

      {/* Selected file preview */}
      {selectedFile && !scanResult && (
        <div className="card mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Selected Image</h3>
            <button
              onClick={clearSelection}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Clear
            </button>
          </div>
          
          <div className="mb-4">
            <img
              src={URL.createObjectURL(selectedFile)}
              alt="Selected prescription"
              className="max-w-full h-auto rounded-lg border border-gray-200"
              style={{ maxHeight: '400px' }}
            />
          </div>
          
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              <p>{selectedFile.name}</p>
              <p>{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
            </div>
            
            <button
              onClick={handleScan}
              disabled={isScanning}
              className="btn btn-primary"
            >
              {isScanning ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Scanning...
                </>
              ) : (
                'Scan for Interactions'
              )}
            </button>
          </div>
        </div>
      )}

      {/* Scan results */}
      {scanResult && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Scan Results</h3>
            <button
              onClick={clearSelection}
              className="btn btn-secondary"
            >
              Scan Another
            </button>
          </div>

          {/* Extracted medications */}
          {scanResult.medications && scanResult.medications.length > 0 && (
            <div className="card">
              <h4 className="text-md font-semibold text-gray-900 mb-4">
                Detected Medications
              </h4>
              <div className="space-y-3">
                {scanResult.medications.map((medication, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h5 className="font-semibold text-gray-900">{medication.name}</h5>
                        {medication.generic_name && (
                          <p className="text-sm text-gray-600">
                            Generic: {medication.generic_name}
                          </p>
                        )}
                        {medication.dosage && (
                          <p className="text-sm text-gray-600">
                            Dosage: {medication.dosage}
                          </p>
                        )}
                        {medication.frequency && (
                          <p className="text-sm text-gray-600">
                            Frequency: {medication.frequency}
                          </p>
                        )}
                        <div className="mt-2">
                          <span className="text-xs text-gray-500">
                            Confidence: {(medication.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={() => handleAddMedication(medication)}
                        className="btn btn-primary btn-sm ml-4"
                      >
                        Add to Profile
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Interaction alerts */}
          {scanResult.interactions && scanResult.interactions.length > 0 && (
            <div className="card">
              <div className="flex items-center space-x-2 mb-4">
                <AlertTriangle className="h-5 w-5 text-warning-600" />
                <h4 className="text-md font-semibold text-gray-900">
                  Interaction Alerts ({scanResult.interactions.length})
                </h4>
              </div>
              <div className="space-y-4">
                {scanResult.interactions.map((interaction, index) => (
                  <InteractionAlert key={index} interaction={interaction} />
                ))}
              </div>
            </div>
          )}

          {/* No interactions found */}
          {scanResult.interactions && scanResult.interactions.length === 0 && (
            <div className="card text-center py-8">
              <CheckCircle className="h-12 w-12 text-success-600 mx-auto mb-4" />
              <h4 className="text-lg font-semibold text-gray-900 mb-2">
                No Interactions Detected
              </h4>
              <p className="text-gray-600">
                The scanned medications don't appear to have any known interactions
                with your current medications.
              </p>
            </div>
          )}

          {/* Recommendations */}
          {scanResult.recommendations && scanResult.recommendations.length > 0 && (
            <div className="card bg-blue-50 border-blue-200">
              <h4 className="text-md font-semibold text-blue-900 mb-3">
                Recommendations
              </h4>
              <ul className="space-y-2">
                {scanResult.recommendations.map((recommendation, index) => (
                  <li key={index} className="text-sm text-blue-800 flex items-start">
                    <span className="w-2 h-2 bg-blue-600 rounded-full mt-2 mr-3 flex-shrink-0" />
                    {recommendation}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Camera modal */}
      {showCamera && (
        <CameraCapture
          onCapture={handleCameraCapture}
          onClose={() => setShowCamera(false)}
        />
      )}

      {/* Instructions */}
      <div className="mt-8 card bg-gray-50">
        <h4 className="text-md font-semibold text-gray-900 mb-3">
          Tips for Better Results
        </h4>
        <ul className="space-y-2 text-sm text-gray-700">
          <li className="flex items-start">
            <span className="w-2 h-2 bg-gray-400 rounded-full mt-2 mr-3 flex-shrink-0" />
            Ensure the prescription label is clearly visible and well-lit
          </li>
          <li className="flex items-start">
            <span className="w-2 h-2 bg-gray-400 rounded-full mt-2 mr-3 flex-shrink-0" />
            Avoid shadows and glare on the label
          </li>
          <li className="flex items-start">
            <span className="w-2 h-2 bg-gray-400 rounded-full mt-2 mr-3 flex-shrink-0" />
            Include the entire label in the image
          </li>
          <li className="flex items-start">
            <span className="w-2 h-2 bg-gray-400 rounded-full mt-2 mr-3 flex-shrink-0" />
            Hold the camera steady to avoid blur
          </li>
        </ul>
      </div>
    </div>
  )
}

export default ScanPage