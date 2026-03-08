import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, act, waitFor } from '@testing-library/react'
import { ToastProvider, useToast } from './Toast'

function ToastTrigger({ message, type }) {
  const toast = useToast()
  return <button onClick={() => toast(message, type)}>Show toast</button>
}

function renderWithProvider(message = 'Something went wrong', type = 'error') {
  return render(
    <ToastProvider>
      <ToastTrigger message={message} type={type} />
    </ToastProvider>
  )
}

describe('ToastProvider', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('shows a toast when triggered', async () => {
    renderWithProvider('Something went wrong')
    fireEvent.click(screen.getByText('Show toast'))
    expect(screen.getByRole('alert')).toHaveTextContent('Something went wrong')
  })

  it('renders with toast-error class for error type', () => {
    renderWithProvider('An error occurred', 'error')
    fireEvent.click(screen.getByText('Show toast'))
    expect(screen.getByRole('alert')).toHaveClass('toast-error')
  })

  it('dismisses the toast when clicked', () => {
    renderWithProvider('Click to dismiss')
    fireEvent.click(screen.getByText('Show toast'))
    const alert = screen.getByRole('alert')
    fireEvent.click(alert)
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('auto-dismisses toast after 4 seconds', async () => {
    renderWithProvider('Auto-dismiss me')
    fireEvent.click(screen.getByText('Show toast'))
    expect(screen.getByRole('alert')).toBeInTheDocument()

    act(() => { vi.advanceTimersByTime(4000) })
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('does not auto-dismiss before 4 seconds', () => {
    renderWithProvider('Still here')
    fireEvent.click(screen.getByText('Show toast'))

    act(() => { vi.advanceTimersByTime(3999) })
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('can show multiple toasts at once', () => {
    render(
      <ToastProvider>
        <ToastTrigger message="First error" />
        <ToastTrigger message="Second error" />
      </ToastProvider>
    )
    const buttons = screen.getAllByText('Show toast')
    fireEvent.click(buttons[0])
    fireEvent.click(buttons[1])
    const alerts = screen.getAllByRole('alert')
    expect(alerts).toHaveLength(2)
  })

  it('throws if useToast is used outside ToastProvider', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    function BadComponent() {
      useToast()
      return null
    }
    expect(() => render(<BadComponent />)).toThrow('useToast must be used within a ToastProvider')
    spy.mockRestore()
  })
})
