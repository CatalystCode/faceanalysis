import { Action } from 'redux';
export const ADD_IMAGE = "ADD_IMAGE";
export const SHOW_IMAGE = "SHOW_IMAGE";
export const SET_SUBJECT = "SET_SUBJECT";
export const SET_TARGET = "SET_TARGET";
export const CLEAR_CANDIDATES = "CLEAR_CANDIDATES";

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

