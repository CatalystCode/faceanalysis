import { Action } from 'redux';
export const ADD_IMAGE = "ADD_IMAGE";

// export declare interface Actions {
//   type:string;
// }

export interface ImageProperties {
  url: string;
  alt?: string;
  width: number;
  height: number
}

export interface ActionWithPayload<T> extends Action {
  payload: T;
}
