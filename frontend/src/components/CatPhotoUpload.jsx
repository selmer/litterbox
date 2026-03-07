import { useRef, useState } from 'react'

const MAX_DIMENSION = 1000
const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/avif', 'image/bmp', 'image/tiff']

function compressImage(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const img = new Image()
      img.onload = () => {
        let { width, height } = img
        if (width > MAX_DIMENSION || height > MAX_DIMENSION) {
          if (width > height) {
            height = Math.round((height * MAX_DIMENSION) / width)
            width = MAX_DIMENSION
          } else {
            width = Math.round((width * MAX_DIMENSION) / height)
            height = MAX_DIMENSION
          }
        }
        const canvas = document.createElement('canvas')
        canvas.width = width
        canvas.height = height
        canvas.getContext('2d').drawImage(img, 0, 0, width, height)
        resolve(canvas.toDataURL('image/jpeg', 0.85))
      }
      img.onerror = () => reject(new Error('Could not load image'))
      img.src = e.target.result
    }
    reader.onerror = () => reject(new Error('Could not read file'))
    reader.readAsDataURL(file)
  })
}

export default function CatPhotoUpload({ catName, onClose, onSave }) {
  const [error, setError] = useState(null)
  const [preview, setPreview] = useState(null)
  const [processing, setProcessing] = useState(false)
  const inputRef = useRef(null)

  async function handleFile(e) {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.type.startsWith('image/') || !ACCEPTED_TYPES.includes(file.type)) {
      setError('Please select a valid image file (JPEG, PNG, GIF, WebP, etc.)')
      e.target.value = ''
      return
    }

    setError(null)
    setProcessing(true)
    try {
      const compressed = await compressImage(file)
      setPreview(compressed)
    } catch {
      setError('Failed to process image. Please try a different file.')
    } finally {
      setProcessing(false)
      e.target.value = ''
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-title">Cat photo</div>
        <p className="text-muted" style={{ fontSize: 13, marginBottom: 16 }}>
          {catName ? `Upload a photo of ${catName}` : 'Upload a photo of your cat'}, or use the
          default icon. Large images are automatically compressed to max {MAX_DIMENSION}×{MAX_DIMENSION}px.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {preview && (
            <div style={{ textAlign: 'center' }}>
              <img
                src={preview}
                alt="Preview"
                style={{ maxWidth: '100%', maxHeight: 200, borderRadius: 8, objectFit: 'cover' }}
              />
            </div>
          )}

          <button
            className="btn btn-secondary w-full"
            onClick={() => inputRef.current?.click()}
            disabled={processing}
          >
            {processing ? 'Processing…' : preview ? 'Choose different photo' : 'Choose photo'}
          </button>

          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            onChange={handleFile}
          />

          {error && (
            <p style={{ fontSize: 12, color: 'var(--red)', margin: 0 }}>{error}</p>
          )}

          {preview && (
            <button className="btn btn-primary w-full" onClick={() => onSave(preview)}>
              Use this photo
            </button>
          )}

          <button className="btn btn-secondary w-full" onClick={() => onSave(null)}>
            Use default icon
          </button>

          <button className="btn btn-secondary w-full" onClick={onClose}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
