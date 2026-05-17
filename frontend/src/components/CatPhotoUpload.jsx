import { useRef, useState, useEffect } from 'react'
import { ModalShell } from './ui'

const MAX_DIMENSION = 1000
const CANVAS_MAX = 320
const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/avif', 'image/bmp', 'image/tiff']

function loadImage(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const img = new Image()
      img.onload = () => resolve(img)
      img.onerror = () => reject(new Error('Could not load image'))
      img.src = e.target.result
    }
    reader.onerror = () => reject(new Error('Could not read file'))
    reader.readAsDataURL(file)
  })
}

function cropAndCompress(img, srcX, srcY, srcW, srcH) {
  let width = srcW
  let height = srcH
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
  const ctx = canvas.getContext('2d')
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, width, height)
  ctx.drawImage(img, srcX, srcY, srcW, srcH, 0, 0, width, height)
  return canvas.toDataURL('image/jpeg', 0.85)
}

export default function CatPhotoUpload({ catName, onClose, onSave }) {
  const [stage, setStage] = useState('idle') // 'idle' | 'crop' | 'preview'
  const [preview, setPreview] = useState(null)
  const [error, setError] = useState(null)
  const [processing, setProcessing] = useState(false)

  const inputRef = useRef(null)
  const canvasRef = useRef(null)
  const imgRef = useRef(null)
  const scaleRef = useRef(1)
  const dragRef = useRef(null)
  const rectRef = useRef(null)

  function drawCanvas() {
    const canvas = canvasRef.current
    const img = imgRef.current
    if (!canvas || !img) return
    const ctx = canvas.getContext('2d')
    const cw = canvas.width
    const ch = canvas.height

    ctx.clearRect(0, 0, cw, ch)
    ctx.drawImage(img, 0, 0, cw, ch)

    const rect = rectRef.current
    if (rect && rect.w > 0 && rect.h > 0) {
      // Darken outside crop area
      ctx.fillStyle = 'rgba(0,0,0,0.55)'
      ctx.beginPath()
      ctx.rect(0, 0, cw, ch)
      ctx.rect(rect.x, rect.y, rect.w, rect.h)
      ctx.fill('evenodd')

      // Re-draw image inside crop area at full brightness
      const scale = scaleRef.current
      ctx.drawImage(
        img,
        rect.x / scale, rect.y / scale, rect.w / scale, rect.h / scale,
        rect.x, rect.y, rect.w, rect.h
      )

      // Border
      ctx.strokeStyle = 'white'
      ctx.lineWidth = 1.5
      ctx.strokeRect(rect.x, rect.y, rect.w, rect.h)

      // Corner handles
      const hs = 8
      ctx.fillStyle = 'white'
      ;[
        [rect.x, rect.y],
        [rect.x + rect.w - hs, rect.y],
        [rect.x, rect.y + rect.h - hs],
        [rect.x + rect.w - hs, rect.y + rect.h - hs],
      ].forEach(([hx, hy]) => ctx.fillRect(hx, hy, hs, hs))
    }
  }

  useEffect(() => {
    if (stage === 'crop' && imgRef.current) {
      requestAnimationFrame(() => {
        const canvas = canvasRef.current
        const img = imgRef.current
        if (!canvas || !img) return
        const scale = Math.min(CANVAS_MAX / img.width, CANVAS_MAX / img.height, 1)
        canvas.width = Math.round(img.width * scale)
        canvas.height = Math.round(img.height * scale)
        scaleRef.current = scale
        if (!rectRef.current) {
          rectRef.current = { x: 0, y: 0, w: canvas.width, h: canvas.height }
        }
        drawCanvas()
      })
    }
  }, [stage])

  function getCanvasCoords(e) {
    const canvas = canvasRef.current
    const bounds = canvas.getBoundingClientRect()
    const clientX = e.touches ? e.touches[0].clientX : e.clientX
    const clientY = e.touches ? e.touches[0].clientY : e.clientY
    return {
      x: Math.max(0, Math.min(canvas.width, (clientX - bounds.left) * (canvas.width / bounds.width))),
      y: Math.max(0, Math.min(canvas.height, (clientY - bounds.top) * (canvas.height / bounds.height))),
    }
  }

  function handlePointerDown(e) {
    e.preventDefault()
    const { x, y } = getCanvasCoords(e)
    dragRef.current = { startX: x, startY: y }
    rectRef.current = { x, y, w: 0, h: 0 }
    drawCanvas()
  }

  function handlePointerMove(e) {
    if (!dragRef.current) return
    e.preventDefault()
    const { x, y } = getCanvasCoords(e)
    const { startX, startY } = dragRef.current
    rectRef.current = {
      x: Math.min(startX, x),
      y: Math.min(startY, y),
      w: Math.abs(x - startX),
      h: Math.abs(y - startY),
    }
    drawCanvas()
  }

  function handlePointerUp() {
    dragRef.current = null
  }

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
      const img = await loadImage(file)
      imgRef.current = img
      rectRef.current = null
      setStage('crop')
    } catch {
      setError('Failed to process image. Please try a different file.')
    } finally {
      setProcessing(false)
      e.target.value = ''
    }
  }

  function applyCrop() {
    const img = imgRef.current
    if (!img) return
    const rect = rectRef.current
    const scale = scaleRef.current

    let srcX, srcY, srcW, srcH
    if (!rect || rect.w < 5 || rect.h < 5) {
      srcX = 0; srcY = 0; srcW = img.width; srcH = img.height
    } else {
      srcX = Math.round(rect.x / scale)
      srcY = Math.round(rect.y / scale)
      srcW = Math.round(rect.w / scale)
      srcH = Math.round(rect.h / scale)
    }

    setPreview(cropAndCompress(img, srcX, srcY, srcW, srcH))
    setStage('preview')
  }

  function resetCropSelection() {
    const canvas = canvasRef.current
    if (!canvas) return
    rectRef.current = { x: 0, y: 0, w: canvas.width, h: canvas.height }
    drawCanvas()
  }

  return (
    <ModalShell title="Cat photo" onClose={onClose} className={stage === 'crop' ? 'modal--crop' : ''}>

        {stage === 'idle' && (
          <>
            <p className="modal-description">
              {catName ? `Upload a photo of ${catName}` : 'Upload a photo of your cat'}, or use the
              default icon. Large images are automatically compressed to max {MAX_DIMENSION}×{MAX_DIMENSION}px.
            </p>
            <div className="modal-stack">
              <button
                className="btn btn-secondary w-full"
                onClick={() => inputRef.current?.click()}
                disabled={processing}
              >
                {processing ? 'Processing…' : 'Choose photo'}
              </button>
              <button className="btn btn-secondary w-full" onClick={() => onSave(null)}>
                Use default icon
              </button>
              <button className="btn btn-secondary w-full" onClick={onClose}>
                Cancel
              </button>
            </div>
          </>
        )}

        {stage === 'crop' && (
          <>
            <p className="modal-description modal-description--tight">
              Drag to select the area to keep. Leave unselected to use the full image.
            </p>
            <div className="photo-cropper">
              <canvas
                ref={canvasRef}
                className="photo-cropper__canvas"
                onMouseDown={handlePointerDown}
                onMouseMove={handlePointerMove}
                onMouseUp={handlePointerUp}
                onMouseLeave={handlePointerUp}
                onTouchStart={handlePointerDown}
                onTouchMove={handlePointerMove}
                onTouchEnd={handlePointerUp}
              />
            </div>
            <div className="modal-stack">
              <div className="modal-actions">
                <button className="btn btn-secondary" onClick={resetCropSelection}>
                  Reset
                </button>
                <button className="btn btn-primary modal-action-wide" onClick={applyCrop}>
                  Apply crop
                </button>
              </div>
              <button
                className="btn btn-secondary w-full"
                onClick={() => { setStage('idle'); imgRef.current = null }}
              >
                Back
              </button>
            </div>
          </>
        )}

        {stage === 'preview' && (
          <>
            <p className="modal-description">
              Looking good! Save this photo or go back to adjust the crop.
            </p>
            <div className="modal-stack">
              <div className="photo-preview">
                <img
                  src={preview}
                  alt="Preview"
                  className="photo-preview__image"
                />
              </div>
              <button className="btn btn-primary w-full" onClick={() => onSave(preview)}>
                Use this photo
              </button>
              <button className="btn btn-secondary w-full" onClick={() => setStage('crop')}>
                Crop differently
              </button>
              <button className="btn btn-secondary w-full" onClick={() => inputRef.current?.click()}>
                Choose different photo
              </button>
              <button className="btn btn-secondary w-full" onClick={() => onSave(null)}>
                Use default icon
              </button>
              <button className="btn btn-secondary w-full" onClick={onClose}>
                Cancel
              </button>
            </div>
          </>
        )}

        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="visually-hidden-input"
          onChange={handleFile}
        />
        {error && (
          <p className="form-error mt-2">{error}</p>
        )}
    </ModalShell>
  )
}
