// src/app/app.config.ts

import { ApplicationConfig, provideZonelessChangeDetection } from '@angular/core'; // <--- CORRECCIÓN AQUÍ
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';
import { provideClientHydration } from '@angular/platform-browser';

import { provideHttpClient, withFetch } from '@angular/common/http';

export const appConfig: ApplicationConfig = {
  providers: [
    // --- LÍNEA CORREGIDA PARA TU PROYECTO "ZONELESS" ---
    provideZonelessChangeDetection(), 
    
    provideRouter(routes), 
    provideClientHydration(),
    provideHttpClient(withFetch()), 
  ]
};