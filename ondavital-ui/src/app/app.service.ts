// src/app/app.service.ts

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';

// Define la estructura de los datos que esperamos de la API
export interface EcgSample {
  ecg_plot: string;
  beat_index: number;
}

export interface ClassificationResult {
  prediction: string;
  confidence: string;
  confidence_percent: number;
  true_label: string;
  is_correct: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class AppService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  // Pide una nueva muestra de ECG
  getNewSample(): Observable<EcgSample> {
    return this.http.get<EcgSample>(this.apiUrl);
  }

  // Envía un índice para clasificar
  classifySample(beatIndex: number): Observable<ClassificationResult> {
    return this.http.post<ClassificationResult>(this.apiUrl, { beat_index: beatIndex });
  }
}