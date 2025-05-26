/// <reference types="vite/client" />

// More robust Vue component typing for Volar
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  import type { AllowedComponentProps, ComponentCustomProps, VNodeProps } from 'vue'

  // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/ban-types
  const component: DefineComponent<{}, {}, any> & {
    new (): {
      $props: AllowedComponentProps & ComponentCustomProps & VNodeProps
    }
  }
  export default component
}
