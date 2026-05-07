p3 = r"""
\section{Statistical Analysis Framework}

\subsection{First-Order Moment Statistics}
For a single image channel $\{x(m,n)\}$ with $N = M_1 M_2$ pixels:
\begin{align}
\mu_X &= \frac{1}{N}\sum_{m,n} x(m,n) \\
\sigma_X^2 &= \frac{1}{N}\sum_{m,n}(x(m,n)-\mu_X)^2 \\
\gamma_1 &= \frac{1}{N\sigma_X^3}\sum_{m,n}(x(m,n)-\mu_X)^3 \quad\text{(skewness)}\\
\gamma_2 &= \frac{1}{N\sigma_X^4}\sum_{m,n}(x(m,n)-\mu_X)^4 - 3 \quad\text{(excess kurtosis)}
\end{align}
Skewness measures asymmetry of the intensity histogram. Excess kurtosis measures tail heaviness relative to a Gaussian ($\gamma_2=0$ for Gaussian; $\gamma_2 > 0$ for heavy-tailed distributions such as Laplacian). These serve as noise-type indicators in addition to the dedicated noise classifier.

\subsection{Signal-to-Noise Ratio}
The system defines SNR using the mean as the signal power estimate and variance as noise power:
\begin{equation}
\text{SNR} = \frac{\mu_X^2}{\sigma_X^2}, \qquad \text{SNR}_{dB} = 10\log_{10}\!\left(\frac{\mu_X^2}{\sigma_X^2}\right)
\end{equation}
This definition follows from modeling the image as signal $\mu_X$ plus zero-mean noise of variance $\sigma_X^2$. Per-step improvement is computed as:
\begin{equation}
\Delta\text{SNR}_{dB} = \text{SNR}_{dB}^{\text{output}} - \text{SNR}_{dB}^{\text{input}}
\end{equation}

\subsection{Shannon Entropy}
Entropy measures information content from the 256-bin normalized histogram $\{p_k\}_{k=0}^{255}$:
\begin{equation}
H = -\sum_{k=0}^{255} p_k \log_2 p_k \quad \text{(bits)}
\end{equation}
Entropy increases after histogram equalization (histogram becomes more uniform) and decreases after aggressive smoothing (less variation in pixel values). The theoretical maximum for 8-bit images is $H=8$ bits.

\subsection{Normalized 2-D Autocorrelation}
The normalized autocorrelation function (ACF) of the zero-mean luminance field $\tilde{Y}(m,n) = Y(m,n) - \mu_Y$ at lag $(\Delta m, \Delta n)$:
\begin{equation}
R_{YY}[\Delta m, \Delta n] = \frac{\displaystyle\sum_{m,n}\tilde{Y}(m,n)\,\tilde{Y}(m+\Delta m,\,n+\Delta n)}{N\sigma_Y^2}
\end{equation}
By the Wiener-Khinchin theorem, the ACF and PSD form a Fourier transform pair:
\begin{equation}
S_Y(u,v) = \mathcal{F}\{R_{YY}[\Delta m,\Delta n]\}
\end{equation}
White noise has $R_{YY}[\Delta m,\Delta n] = \sigma_n^2\,\delta[\Delta m]\,\delta[\Delta n]$ (zero correlation at all non-zero lags). Natural images have high ACF at small lags, reflecting spatial smoothness. The system reports ACF at lags $(1,0)$, $(0,1)$, and $(1,1)$.

\subsection{2-D Autocorrelation Visualization}
The full 2-D ACF is computed via \texttt{scipy.signal.correlate2d} and cropped to a $64\times64$ center patch for visualization. The map is normalized to $[-1,1]$ and displayed using a RdBu colormap. A peaked center spike with rapid fall-off indicates near-white noise; a broad main lobe indicates strongly spatially correlated content.

\subsection{BT.601 Luminance Extraction}
For RGB images, scalar statistics are computed on the luma channel:
\begin{equation}
Y(m,n) = 0.299\,R(m,n) + 0.587\,G(m,n) + 0.114\,B(m,n)
\end{equation}
These weights follow the ITU-R BT.601 standard and reflect the human visual system's higher sensitivity to green wavelengths.

\section{System Architecture}

\subsection{Backend Stack}
The processing pipeline is implemented as a Python 3.11 FastAPI application, following a service-oriented architecture:

\begin{table}[h]
\caption{Backend Module Responsibilities}
\centering
\begin{tabular}{@{}p{3.5cm}p{4.5cm}@{}}
\toprule
\textbf{Module} & \textbf{Responsibility} \\
\midrule
\texttt{main.py} & App entry, CORS, lifespan \\
\texttt{routers/upload.py} & Image ingestion, session creation \\
\texttt{routers/process.py} & Pipeline orchestration \\
\texttt{services/noise\_detector.py} & MAD + S\&P + Laplacian classifier \\
\texttt{services/filters.py} & Gaussian, Median, Bilateral, Histeq \\
\texttt{services/bayesian\_estimator.py} & MAP/Wiener per-pixel denoising \\
\texttt{services/markov\_field.py} & MRF-ICM smoothing \\
\texttt{services/stat\_analyzer.py} & All statistical metrics \\
\texttt{services/visualizer.py} & Matplotlib chart generation \\
\texttt{utils/image\_io.py} & Float32/uint8/base64 conversion \\
\bottomrule
\end{tabular}
\end{table}

\subsection{REST API Endpoints}
\begin{table}[h]
\caption{API Endpoint Summary}
\centering
\begin{tabular}{@{}p{1.5cm}p{3cm}p{3cm}@{}}
\toprule
\textbf{Method} & \textbf{Endpoint} & \textbf{Action} \\
\midrule
POST & \texttt{/api/upload} & Upload image, get session\_id \\
POST & \texttt{/api/process/\{sid\}} & Run pipeline, get results \\
GET  & \texttt{/api/health} & Health check \\
\bottomrule
\end{tabular}
\end{table}

\subsection{Pipeline Data Flow}
Images are stored server-side as float32 NumPy arrays keyed by UUID session IDs. A background \texttt{asyncio} coroutine periodically purges stale sessions. The processing endpoint accepts a JSON body specifying a list of step identifiers and parameters:
\begin{verbatim}
{"steps": ["noise_analysis",
           "gaussian_filter",
           "bayesian_map"],
 "params": {"gaussian_sigma": 1.5,
            "bayesian_noise_var": null}}
\end{verbatim}
Steps execute sequentially; the output image of step $t$ is the input to step $t+1$. Each step returns: filtered image (base64 PNG), statistics dictionary, and chart images (base64 PNG histograms, SNR bar, convergence plot, Wiener gain heatmap).

\subsection{Image Representation}
All internal operations use float32 in $[0,1]$. Conversion pipeline:
\begin{equation}
\text{PIL} \xrightarrow{\div 255} \text{float32} \xrightarrow{\text{process}} \text{float32} \xrightarrow{\times 255} \text{uint8} \xrightarrow{\text{PNG/Base64}} \text{JSON}
\end{equation}
The float32 representation prevents cascading quantization errors across pipeline stages.

\section{Results and Discussion}

\subsection{Filter-Noise Model Correspondence}
Table~\ref{tab:correspondence} summarizes the theoretical optimality of each filter for each noise type.

\begin{table}[h]
\caption{Filter--Noise Model Correspondence}
\label{tab:correspondence}
\centering
\begin{tabular}{@{}llll@{}}
\toprule
\textbf{Filter} & \textbf{Noise Model} & \textbf{Optimality} & \textbf{Complexity} \\
\midrule
Gaussian   & AWGN & LTI / spectral & $O(MN)$ \\
Median     & Laplacian/Impulse & ML $L_1$ & $O(MNK\log K)$ \\
Bilateral  & AWGN + edges & MAP edge-aware & $O(MNK^2)$ \\
Hist. Eq.  & Contrast/Blur & Max entropy & $O(MN)$ \\
Bayesian   & AWGN (Gaussian prior) & MAP = MMSE & $O(MN)$ \\
MRF-ICM    & AWGN (GMRF prior) & MAP-MRF & $O(MNT)$ \\
\bottomrule
\end{tabular}
\end{table}

\subsection{SNR Improvement Analysis}
The system tracks $\text{SNR}_{dB}$ before and after every step. The Bayesian MAP denoiser typically achieves the largest SNR improvement for AWGN because it directly minimizes the posterior risk. The median filter achieves the largest improvement for Salt \& Pepper noise. Bilateral filtering improves SNR while keeping the edge sharpness metric (Laplacian variance) high, unlike Gaussian filtering which degrades it.

\subsection{Entropy Behavior}
Histogram equalization reliably increases entropy toward $H=8$ bits. Conversely, Gaussian and Bayesian MAP filtering reduce entropy slightly as the smoothed output has a more concentrated histogram. The entropy reports at each step allow quantitative verification of these theoretical predictions.

\subsection{Autocorrelation Signatures}
A noisy image typically shows near-zero ACF at non-zero lags ($R_{YY}[1,0] \approx 0$), consistent with white noise. After Gaussian or Bayesian MAP filtering, ACF at lag $(1,0)$ increases (the output becomes spatially correlated), reflecting the smoothing operation. After MRF-ICM, ACF increases more strongly due to the explicit spatial coupling enforced by $\beta$.

\section{Conclusion}

This paper presented a modular probabilistic signal processing framework for image denoising and enhancement, implemented as a production-grade REST API. The following contributions were made:

\begin{enumerate}
\item A three-feature noise classifier combining MAD, impulse density, and Laplacian variance, providing automatic filter recommendations.
\item Six filters derived from first principles: Gaussian (LTI/PSD), Median ($L_1$/ML), Bilateral (edge-preserving MAP), Histogram Equalization (entropy maximization), Bayesian MAP (Wiener filter), and MRF-ICM (GMRF prior).
\item A spatially adaptive Bayesian MAP denoiser with closed-form Wiener gain $K = \sigma_x^2/(\sigma_x^2+\sigma_n^2)$ estimated locally in $5\times5$ windows.
\item A vectorized MRF-ICM implementation with convergence tracking.
\item A comprehensive statistical analysis suite: entropy, SNR, skewness, excess kurtosis, and 2-D normalized autocorrelation.
\item A RESTful FastAPI service enabling pipeline composition, per-step reporting, and session-based image management.
\end{enumerate}

Future work includes: extending the MRF prior to non-quadratic (Total Variation) potentials for sharper edge preservation; wavelet-domain soft-thresholding (Donoho-Johnstone); incorporating deep-learning denoisers (DnCNN, FFDNet) as optional pipeline stages; and extending the noise classifier to handle Poisson (photon shot) and speckle noise models.

\begin{thebibliography}{00}
\bibitem{papoulis} A. Papoulis and S. U. Pillai, \textit{Probability, Random Variables, and Stochastic Processes}, 4th~ed. New York: McGraw-Hill, 2002.
\bibitem{gonzalez} R. C. Gonzalez and R. E. Woods, \textit{Digital Image Processing}, 4th~ed. London: Pearson, 2018.
\bibitem{wiener} N. Wiener, \textit{Extrapolation, Interpolation, and Smoothing of Stationary Time Series}. Cambridge, MA: MIT Press, 1949.
\bibitem{geman} S. Geman and D. Geman, ``Stochastic relaxation, Gibbs distributions, and the Bayesian restoration of images,'' \textit{IEEE Trans. Pattern Anal. Mach. Intell.}, vol.~PAMI-6, no.~6, pp.~721--741, Nov.~1984. \href{https://doi.org/10.1109/TPAMI.1984.4767596}{doi:10.1109/TPAMI.1984.4767596}
\bibitem{tomasi} C. Tomasi and R. Manduchi, ``Bilateral filtering for gray and color images,'' in \textit{Proc. IEEE ICCV}, Bombay, India, 1998, pp.~839--846. \href{https://doi.org/10.1109/ICCV.1998.710815}{doi:10.1109/ICCV.1998.710815}
\bibitem{besag} J. Besag, ``On the statistical analysis of dirty pictures,'' \textit{J. Roy. Stat. Soc.~B}, vol.~48, no.~3, pp.~259--302, 1986.
\bibitem{shannon} C.~E. Shannon, ``A mathematical theory of communication,'' \textit{Bell Syst. Tech. J.}, vol.~27, pp.~379--423, 1948. \href{https://doi.org/10.1002/j.1538-7305.1948.tb01338.x}{doi:10.1002/j.1538-7305.1948.tb01338.x}
\bibitem{donoho} D.~L. Donoho and I.~M. Johnstone, ``Ideal spatial adaptation by wavelet shrinkage,'' \textit{Biometrika}, vol.~81, no.~3, pp.~425--455, 1994. \href{https://doi.org/10.1093/biomet/81.3.425}{doi:10.1093/biomet/81.3.425}
\bibitem{scipy} P. Virtanen \textit{et al.}, ``SciPy 1.0: Fundamental algorithms for scientific computing in Python,'' \textit{Nature Methods}, vol.~17, pp.~261--272, 2020. \href{https://doi.org/10.1038/s41592-019-0686-2}{doi:10.1038/s41592-019-0686-2}
\bibitem{opencv} G. Bradski, ``The OpenCV library,'' \textit{Dr.~Dobb's J. Software Tools}, vol.~25, no.~11, pp.~120--125, 2000. \href{https://opencv.org}{opencv.org}
\bibitem{fastapi} S. Ramirez, ``FastAPI framework,'' 2019. [Online]. Available: \href{https://fastapi.tiangolo.com}{https://fastapi.tiangolo.com}
\end{thebibliography}

\end{document}
"""
with open("report.tex","a",encoding="utf-8") as f:
    f.write("\n" + p3.strip())
print("Part 3 appended — report.tex complete.")
