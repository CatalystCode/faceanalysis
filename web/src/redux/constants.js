import axios from 'axios';

export function getClient() {
  const restUrl = 'http://localhost:3000/api';
  const client = axios.create({
    baseURL: restUrl,
    responseType: 'json'
  });

  return client;
}