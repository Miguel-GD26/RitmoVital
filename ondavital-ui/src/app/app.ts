// src/app/app.ts

import { Component, OnInit, ChangeDetectorRef } from '@angular/core'; // 1. Importar ChangeDetectorRef
import { CommonModule } from '@angular/common';
import { AppService, EcgSample, ClassificationResult } from './app.service';
import { DomSanitizer, SafeUrl } from '@angular/platform-browser';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './app.html',
  styleUrls: ['./app.css']
})
export class App implements OnInit {
  
  isLoading = true;
  isClassifying = false;
  errorMessage: string | null = null;
  currentSample: EcgSample | null = null;
  classificationResult: ClassificationResult | null = null;
  ecgPlotUrl: SafeUrl | null = null;

  constructor(
    private apiService: AppService, 
    private sanitizer: DomSanitizer,
    private cdr: ChangeDetectorRef // 2. Inyectar ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadNewSample();
  }

  loadNewSample(): void {
    this.isLoading = true;
    this.classificationResult = null;
    this.ecgPlotUrl = null;
    this.errorMessage = null;

    this.apiService.getNewSample().subscribe({
      next: (data) => {
        this.currentSample = data;
        this.ecgPlotUrl = this.sanitizer.bypassSecurityTrustUrl('data:image/png;base64,' + data.ecg_plot);
        this.isLoading = false;
        this.cdr.detectChanges(); // También es bueno ponerlo aquí
      },
      error: (err) => {
        console.error("Error al cargar la muestra:", err);
        this.errorMessage = "Error de conexión. No se pudo cargar una nueva muestra.";
        this.isLoading = false;
        this.cdr.detectChanges();
      }
    });
  }

  classifyCurrentSample(): void {
    if (!this.currentSample || this.isClassifying) {
      return;
    }

    this.isClassifying = true;
    this.classificationResult = null;
    this.errorMessage = null;

    this.apiService.classifySample(this.currentSample.beat_index).subscribe({
      next: (result) => {
        this.classificationResult = result;
        this.isClassifying = false;
        
        // 3. Forzar la actualización de la vista
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error("Error al clasificar:", err);
        this.errorMessage = "Ocurrió un error durante el análisis.";
        this.isClassifying = false;
        this.cdr.detectChanges();
      }
    });
  }
}