interface Option {
  value: string
  label: string
}

interface BaseProps {
  label: string
  name: string
  error?: string
  required?: boolean
}

interface TextFieldProps extends BaseProps {
  type: 'text' | 'number'
  value: string | number
  onChange: (value: string) => void
  placeholder?: string
}

interface TextareaFieldProps extends BaseProps {
  type: 'textarea'
  value: string
  onChange: (value: string) => void
  placeholder?: string
  rows?: number
}

interface SelectFieldProps extends BaseProps {
  type: 'select'
  value: string
  onChange: (value: string) => void
  options: Option[]
}

interface MultiSelectFieldProps extends BaseProps {
  type: 'multiselect'
  value: string[]
  onChange: (value: string[]) => void
  options: Option[]
}

type FormFieldProps =
  | TextFieldProps
  | TextareaFieldProps
  | SelectFieldProps
  | MultiSelectFieldProps

const baseInputStyles =
  'block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 shadow-sm placeholder:text-gray-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500'
const errorInputStyles =
  'border-red-300 focus:border-red-500 focus:ring-red-500'

export default function FormField(props: FormFieldProps) {
  const { label, name, error, required } = props
  const inputId = `field-${name}`

  return (
    <div>
      <label
        htmlFor={inputId}
        className="mb-1 block text-sm font-medium text-gray-700"
      >
        {label}
        {required && <span className="ml-0.5 text-red-500">*</span>}
      </label>

      {props.type === 'text' || props.type === 'number' ? (
        <input
          id={inputId}
          name={name}
          type={props.type}
          value={props.value}
          onChange={(e) => props.onChange(e.target.value)}
          placeholder={props.placeholder}
          className={`${baseInputStyles} ${error ? errorInputStyles : ''}`}
        />
      ) : props.type === 'textarea' ? (
        <textarea
          id={inputId}
          name={name}
          value={props.value}
          onChange={(e) => props.onChange(e.target.value)}
          placeholder={props.placeholder}
          rows={props.rows ?? 3}
          className={`${baseInputStyles} ${error ? errorInputStyles : ''}`}
        />
      ) : props.type === 'select' ? (
        <select
          id={inputId}
          name={name}
          value={props.value}
          onChange={(e) => props.onChange(e.target.value)}
          className={`${baseInputStyles} ${error ? errorInputStyles : ''}`}
        >
          <option value="">Select...</option>
          {props.options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      ) : props.type === 'multiselect' ? (
        <div className="flex flex-wrap gap-2 rounded-lg border border-gray-300 p-2">
          {props.options.length === 0 && (
            <span className="px-1 text-sm text-gray-400">
              No options available
            </span>
          )}
          {props.options.map((opt) => {
            const selected = props.value.includes(opt.value)
            return (
              <button
                key={opt.value}
                type="button"
                onClick={() => {
                  if (selected) {
                    props.onChange(props.value.filter((v) => v !== opt.value))
                  } else {
                    props.onChange([...props.value, opt.value])
                  }
                }}
                className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                  selected
                    ? 'bg-indigo-100 text-indigo-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {opt.label}
              </button>
            )
          })}
        </div>
      ) : null}

      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  )
}
