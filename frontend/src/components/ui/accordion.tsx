import * as React from "react"
import { ChevronDown } from "lucide-react"
import { cn } from "@/lib/utils"

const AccordionContext = React.createContext<{
  value: string | undefined
  onValueChange: (value: string | undefined) => void
}>({ value: undefined, onValueChange: () => {} })

const AccordionItemContext = React.createContext<{ value: string }>({ value: "" })

interface AccordionProps {
  type?: "single" | "multiple"
  collapsible?: boolean
  value?: string
  onValueChange?: (value: string | undefined) => void
  defaultValue?: string
  className?: string
  children: React.ReactNode
}

const Accordion = React.forwardRef<HTMLDivElement, AccordionProps>(
  ({ type = "single", collapsible = false, value: controlledValue, onValueChange, defaultValue, className, children, ...props }, ref) => {
    const [internalValue, setInternalValue] = React.useState<string | undefined>(defaultValue)

    const value = controlledValue !== undefined ? controlledValue : internalValue

    const handleValueChange = React.useCallback((newValue: string | undefined) => {
      if (onValueChange) {
        onValueChange(newValue)
      } else {
        setInternalValue(newValue)
      }
    }, [onValueChange])

    return (
      <AccordionContext.Provider value={{ value, onValueChange: handleValueChange }}>
        <div ref={ref} className={cn("space-y-1", className)} {...props}>
          {children}
        </div>
      </AccordionContext.Provider>
    )
  }
)
Accordion.displayName = "Accordion"

interface AccordionItemProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string
}

const AccordionItem = React.forwardRef<HTMLDivElement, AccordionItemProps>(
  ({ className, value, children, ...props }, ref) => {
    return (
      <AccordionItemContext.Provider value={{ value }}>
        <div
          ref={ref}
          className={cn("border-b", className)}
          {...props}
        >
          {children}
        </div>
      </AccordionItemContext.Provider>
    )
  }
)
AccordionItem.displayName = "AccordionItem"

interface AccordionTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {}

const AccordionTrigger = React.forwardRef<HTMLButtonElement, AccordionTriggerProps>(
  ({ className, children, ...props }, ref) => {
    const { value, onValueChange } = React.useContext(AccordionContext)
    const { value: itemValue } = React.useContext(AccordionItemContext)
    const isOpen = value === itemValue

    return (
      <button
        ref={ref}
        type="button"
        className={cn(
          "flex flex-1 w-full items-center justify-between py-4 font-medium transition-all hover:underline [&[data-state=open]>svg]:rotate-180",
          className
        )}
        onClick={() => onValueChange(isOpen ? undefined : itemValue)}
        data-state={isOpen ? "open" : "closed"}
        {...props}
      >
        {children}
        <ChevronDown className="h-4 w-4 shrink-0 transition-transform duration-200" />
      </button>
    )
  }
)
AccordionTrigger.displayName = "AccordionTrigger"

interface AccordionContentProps extends React.HTMLAttributes<HTMLDivElement> {}

const AccordionContent = React.forwardRef<HTMLDivElement, AccordionContentProps>(
  ({ className, children, ...props }, ref) => {
    const { value } = React.useContext(AccordionContext)
    const { value: itemValue } = React.useContext(AccordionItemContext)
    const isOpen = value === itemValue

    if (!isOpen) return null

    return (
      <div
        ref={ref}
        className={cn("overflow-hidden text-sm pb-4 pt-0", className)}
        {...props}
      >
        {children}
      </div>
    )
  }
)
AccordionContent.displayName = "AccordionContent"

export { Accordion, AccordionItem, AccordionTrigger, AccordionContent }
