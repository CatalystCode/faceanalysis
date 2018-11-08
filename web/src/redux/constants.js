import axios from 'axios';

export const getClient = () => {
  const restUrl = '/api';
  const client = axios.create({
    baseURL: restUrl,
    responseType: 'json'
  });

  return client;
}