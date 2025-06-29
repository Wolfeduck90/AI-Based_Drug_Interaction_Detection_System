import React, { useState, useRef, useCallback } from 'react'
import Webcam from 'react-webcam'
import { Camera, RotateCcw, Check, X } from 'lucide-react'
import toast from 'react-hot-toast'

const CameraCapture = ({ onCapture, onClose }) => {
  const webcamRef = useRef(null)
  const [capturedImage, setCapturedImage] = useState(null)
  const [facingMode, setFacingMode] = useState('environment') // 'user' for front camera

  const videoConstraints = {
    width: 1280,
    height: 720,
    facingMode: facingMode
  }

  const capture = useCallback(() => {
    const imageSrc = webcamRef.current.getScreenshot()
    if (imageSrc) {
      setCapturedImage(imageSrc)
    } else {
      toast.error('Failed to capture image')
    }
  }, [webcamRef])

  const retake = () => {
    setCapturedImage(null)
  }

  const confirm = () => {
    if (capturedImage) {
      // Convert base64 to blob
      fetch(capturedImage)
        .then(res => res.blob())
        .then(blob => {
          const file = new File([blob], 'prescription.jpg', { type: 'image/jpeg' })
          onCapture(file)
        })
        .catch(error => {
          console.error('Error converting image:', error)
          toast.error('Failed to process image')
        })
    }
  }

  const switchCamera = () => {
    setFacingMode(prev => prev === 'user' ? 'environment' : 'user')
  }

  return (
    <div className="fixed inset-0 bg-black z-50 flex flex-col">
      {/* Header */}
      <div className="flex justify-between items-center p-4 text-white">
        <button
          onClick={onClose}
          className="p-2 rounded-full bg-black bg-opacity-50"
        >
          <X className="h-6 w-6" />
        </button>
        <h2 className="text-lg font-semibold">Scan Prescription</h2>
        <button
          onClick={switchCamera}
          className="p-2 rounded-full bg-black bg-opacity-50"
        >
          <RotateCcw className="h-6 w-6" />
        </button>
      </div>

      {/* Camera/Preview */}
      <div className="flex-1 relative">
        {capturedImage ? (
          <img
            src={capturedImage}
            alt="Captured prescription"
            className="w-full h-full object-cover"
          />
        ) : (
          <>
            <Webcam
              ref={webcamRef}
              audio={false}
              screenshotFormat="image/jpeg"
              videoConstraints={videoConstraints}
              className="w-full h-full object-cover"
            />
            
            {/* Camera overlay with guide */}
            <div className="camera-overlay">
              <div className="camera-guide">
                <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 text-white text-sm font-medium">
                  Position prescription label within frame
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Controls */}
      <div className="p-6 flex justify-center items-center space-x-8">
        {capturedImage ? (
          <>
            <button
              onClick={retake}
              className="flex items-center justify-center w-16 h-16 rounded-full bg-gray-600 text-white"
            >
              <RotateCcw className="h-8 w-8" />
            </button>
            <button
              onClick={confirm}
              className="flex items-center justify-center w-16 h-16 rounded-full bg-success-600 text-white"
            >
              <Check className="h-8 w-8" />
            </button>
          </>
        ) : (
          <button
            onClick={capture}
            className="flex items-center justify-center w-20 h-20 rounded-full bg-white text-gray-900 shadow-lg"
          >
            <Camera className="h-10 w-10" />
          </button>
        )}
      </div>

      {/* Instructions */}
      <div className="p-4 text-center text-white text-sm">
        {capturedImage ? (
          <p>Review the captured image and confirm or retake</p>
        ) : (
          <p>Ensure the prescription label is clearly visible and well-lit</p>
        )}
      </div>
    </div>
  )
}

export default CameraCapture