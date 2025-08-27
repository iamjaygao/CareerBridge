import React from 'react';
import {
  TextField,
  TextFieldProps,
  FormControl,
  FormHelperText,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  FormGroup,
  Radio,
  RadioGroup,
  Switch,
} from '@mui/material';
import { Controller, Control } from 'react-hook-form';

interface Option {
  label: string;
  value: string | number | boolean;
}

interface FormFieldProps extends Omit<TextFieldProps, 'type'> {
  name: string;
  control: Control<any>;
  type?: 'text' | 'email' | 'password' | 'select' | 'checkbox' | 'radio' | 'switch' | 'textarea';
  options?: Option[];
  helperText?: string;
}

const FormField: React.FC<FormFieldProps> = ({
  name,
  control,
  type = 'text',
  options,
  helperText,
  ...props
}) => {
  const renderField = (field: any) => {
    switch (type) {
      case 'select':
        return (
          <FormControl fullWidth error={!!field.error}>
            <InputLabel>{props.label}</InputLabel>
            <Select
              {...field}
              {...props}
              value={field.value || ''}
              onChange={e => field.onChange(e.target.value)}
            >
              {options?.map((option) => (
                <MenuItem key={option.value.toString()} value={String(option.value)}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
            {helperText && <FormHelperText>{helperText}</FormHelperText>}
          </FormControl>
        );

      case 'checkbox':
        return (
          <FormGroup>
            {options?.map((option) => (
              <FormControlLabel
                key={option.value.toString()}
                control={
                  <Checkbox
                    checked={Array.isArray(field.value)
                      ? field.value.includes(option.value)
                      : field.value === option.value}
                    onChange={e => {
                      if (Array.isArray(field.value)) {
                        const newValue = e.target.checked
                          ? [...field.value, option.value]
                          : field.value.filter((v: any) => v !== option.value);
                        field.onChange(newValue);
                      } else {
                        field.onChange(e.target.checked);
                      }
                    }}
                  />
                }
                label={option.label}
              />
            ))}
            {helperText && <FormHelperText>{helperText}</FormHelperText>}
          </FormGroup>
        );

      case 'radio':
        return (
          <FormControl component="fieldset">
            <RadioGroup
              {...field}
              onChange={e => field.onChange(e.target.value)}
            >
              {options?.map((option) => (
                <FormControlLabel
                  key={option.value.toString()}
                  value={option.value}
                  control={<Radio />}
                  label={option.label}
                />
              ))}
            </RadioGroup>
            {helperText && <FormHelperText>{helperText}</FormHelperText>}
          </FormControl>
        );

      case 'switch':
        return (
          <FormControlLabel
            control={
              <Switch
                checked={field.value}
                onChange={e => field.onChange(e.target.checked)}
              />
            }
            label={props.label}
          />
        );

      case 'textarea':
        return (
          <TextField
            {...field}
            {...props}
            multiline
            rows={4}
            error={!!field.error}
            helperText={field.error?.message || helperText}
            onChange={e => field.onChange(e.target.value)}
          />
        );

      default:
        return (
          <TextField
            {...field}
            {...props}
            type={type}
            error={!!field.error}
            helperText={field.error?.message || helperText}
            onChange={e => field.onChange(e.target.value)}
          />
        );
    }
  };

  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => renderField({ ...field, error })}
    />
  );
};

export default FormField;