import React from 'react';
import {
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  FormHelperText,
} from '@mui/material';
import { FormField as FormFieldType } from '../../types';

interface FormFieldProps extends FormFieldType {
  value: any;
  onChange: (value: any) => void;
  error?: string;
  disabled?: boolean;
}

const FormField: React.FC<FormFieldProps> = ({
  name,
  label,
  type,
  value,
  onChange,
  error,
  required,
  options,
  disabled,
}) => {
  if (type === 'select' && options) {
    return (
      <FormControl
        fullWidth
        error={!!error}
        required={required}
        disabled={disabled}
        sx={{ mb: 2 }}
      >
        <InputLabel id={`${name}-label`}>{label}</InputLabel>
        <Select
          labelId={`${name}-label`}
          id={name}
          name={name}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          label={label}
        >
          {options.map((option) => (
            <MenuItem key={option.value} value={option.value}>
              {option.label}
            </MenuItem>
          ))}
        </Select>
        {error && <FormHelperText>{error}</FormHelperText>}
      </FormControl>
    );
  }

  if (type === 'textarea') {
    return (
      <TextField
        fullWidth
        id={name}
        name={name}
        label={label}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        error={!!error}
        helperText={error}
        required={required}
        disabled={disabled}
        multiline
        rows={4}
        sx={{ mb: 2 }}
      />
    );
  }

  return (
    <TextField
      fullWidth
      id={name}
      name={name}
      label={label}
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      error={!!error}
      helperText={error}
      required={required}
      disabled={disabled}
      sx={{ mb: 2 }}
    />
  );
};

export default FormField;