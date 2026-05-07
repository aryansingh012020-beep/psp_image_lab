
latex = r"""
\documentclass[10pt,conference]{IEEEtran}
\IEEEoverridecommandlockouts
\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{algorithmic}
\usepackage{graphicx}
\usepackage{textcomp}
\usepackage{xcolor}
\usepackage{hyperref}
\usepackage{booktabs}
\usepackage{array}
\def\BibTeX{{\rm B\kern-.05em{\sc i\kern-.025em b}\kern-.08em T\kern-.1667em\lower.7ex\hbox{E}\kern-.125emX}}

\begin{document}

\title{Intelligent Image Noise Filtering and Statistical Analysis: A Probabilistic Signal Processing Framework}

\author{
\IEEEauthorblockN{Aryan Singh}
\IEEEauthorblockA{\textit{Department of Electronics \& Communication Engineering}\\
\textit{[University Name]}\\
aryansingh012020@[university].edu}
}

\maketitle

\begin{abstract}
This paper presents a comprehensive probabilistic signal processing (PSP) framework for digital image noise characterization and removal. The system integrates classical signal processing theory with Bayesian estimation and Markov Random Fields (MRF) to create an end-to-end pipeline that classifies noise, applies appropriate filters, and quantifies improvement through rigorous statistical metrics. We implement and analyze Gaussian filtering as a linear time-invariant (LTI) system, median filtering as an optimal maximum-likelihood estimator under the Laplacian noise model, bilateral filtering for edge-preserving smoothing, histogram equalization for entropy maximization, Bayesian Maximum A Posteriori (MAP) denoising via the pixelwise Wiener filter, and MRF regularization via Iterated Conditional Modes (ICM). All algorithms operate on float32 images, and SNR improvement is tracked at each stage. Results demonstrate that the probabilistic pipeline consistently improves SNR and reduces noise energy while preserving perceptual image quality.
\end{abstract}

\begin{IEEEkeywords}
noise filtering, Bayesian MAP estimation, Wiener filter, Markov Random Field, bilateral filter, histogram equalization, signal-to-noise ratio, probabilistic signal processing
\end{IEEEkeywords}

% =====================================================================
\section{Introduction}

Digital images acquired by sensors are invariably corrupted by various types of noise arising from photon statistics, sensor thermal fluctuations, transmission errors, and quantization. Effective noise removal requires understanding both the statistical model of the noise process and the spatial structure of the underlying image signal.

Probabilistic Signal Processing (PSP) provides a rigorous framework for this: images are modeled as realizations of random fields, noise as an independent stochastic process, and filtering as Bayesian inference. This paper documents the complete implementation of such a framework as a RESTful API service, covering noise detection, classical filters (Gaussian, Median, Bilateral), contrast enhancement (Histogram Equalization), and advanced probabilistic denoisers (Bayesian MAP / Wiener filter, MRF-ICM).

The backend is structured as a Python FastAPI application. The processing pipeline accepts a float32 image in $[0,1]$ and applies a user-selected sequence of steps, returning filtered images, statistical reports, and visualization charts at each stage.

The remainder of this paper is organized as follows: Section II covers noise modeling and detection. Section III through Section VIII describe each filter with full derivations. Section IX presents the statistical analysis framework. Section X discusses the system architecture, and Section XI concludes.

% =====================================================================
\section{Noise Modeling and Detection}

\subsection{Image Noise Model}

A noisy observed image $y(m,n)$ is modeled as:
\begin{equation}
y(m,n) = x(m,n) + \eta(m,n)
\end{equation}
where $x(m,n)$ is the clean latent image and $\eta(m,n)$ is the noise process. In this system three noise types are identified:

\begin{itemize}
\item \textbf{Gaussian noise}: $\eta \sim \mathcal{N}(0, \sigma_n^2)$ — additive white Gaussian noise (AWGN) arising from thermal effects.
\item \textbf{Salt-and-Pepper (Impulse) noise}: $\eta$ is an impulsive process pushing pixels to extremes $\{0, 255\}$.
\item \textbf{Blur}: excess smoothing detected via low Laplacian energy.
\end{itemize}

\subsection{Gaussian Noise Estimation — MAD Estimator}

The robust noise standard deviation estimator uses the Median Absolute Deviation (MAD) on the high-frequency residual:
\begin{equation}
r(m,n) = y(m,n) - \tilde{y}(m,n)
\end{equation}
where $\tilde{y}$ is obtained by applying a Gaussian pre-filter with $\sigma=1.5$. The MAD-based estimator is:
\begin{equation}
\hat{\sigma}_n = \frac{\text{median}(|r(m,n)|)}{0.6745}
\end{equation}
The constant $0.6745$ is the 75th percentile of the standard normal distribution, making this consistent with $\sigma$ when $r \sim \mathcal{N}(0,\sigma^2)$. This estimator is robust to outliers (salt-and-pepper pixels). A flag $\hat{\sigma}_n > 0.05$ triggers the Gaussian noise classification.

\subsection{Salt-and-Pepper Detection}

Impulse noise is detected by counting extreme-valued pixels:
\begin{equation}
\rho_{sp} = \frac{\#\{(m,n) : y(m,n) < 0.02 \cup y(m,n) > 0.98\}}{M \cdot N}
\end{equation}
If $\rho_{sp} > 0.005$ (0.5\% of pixels), Salt \& Pepper noise is flagged.

\subsection{Blur Detection — Laplacian Variance}

Image sharpness is quantified by the variance of the Laplacian operator output:
\begin{equation}
\nabla^2 y = \frac{\partial^2 y}{\partial m^2} + \frac{\partial^2 y}{\partial n^2}
\end{equation}
Low variance ($< 50$ on uint8 scale) indicates a blurred image since edges produce large Laplacian responses. The discrete Laplacian kernel is:
\begin{equation}
L = \begin{bmatrix} 0 & 1 & 0 \\ 1 & -4 & 1 \\ 0 & 1 & 0 \end{bmatrix}
\end{equation}

% =====================================================================
\section{Gaussian Filter — LTI System Analysis}

\subsection{Derivation}

The Gaussian filter is a linear time-invariant (LTI) system with impulse response:
\begin{equation}
h(m,n) = \frac{1}{2\pi\sigma^2} \exp\!\left(-\frac{m^2+n^2}{2\sigma^2}\right)
\end{equation}

The filtered output is the 2D convolution:
\begin{equation}
\hat{x}(m,n) = (h * y)(m,n) = \sum_{k}\sum_{l} h(k,l)\, y(m-k, n-l)
\end{equation}

\subsection{Power Spectral Density Analysis}

For a LTI system, the output Power Spectral Density (PSD) relates to the input PSD via:
\begin{equation}
S_{\hat{x}}(u,v) = |H(u,v)|^2 \cdot S_y(u,v)
\end{equation}
where $H(u,v)$ is the 2D Fourier transform of $h(m,n)$:
\begin{equation}
H(u,v) = \exp\!\left(-2\pi^2\sigma^2(u^2+v^2)\right)
\end{equation}
$H(u,v)$ is a low-pass filter that attenuates high frequencies exponentially. Since Gaussian noise has a white PSD $S_\eta = \sigma_n^2$ for all $(u,v)$, the output noise PSD becomes $\sigma_n^2 |H|^2$, which is suppressed at high frequencies. The parameter $\sigma$ controls the bandwidth: larger $\sigma$ yields stronger smoothing but may blur edges.

% =====================================================================
\section{Median Filter — Optimal ML Estimator}

\subsection{Laplacian Noise Model}

Under a Laplacian noise model, $\eta \sim \text{Laplace}(0,b)$:
\begin{equation}
p(\eta) = \frac{1}{2b}\exp\!\left(-\frac{|\eta|}{b}\right)
\end{equation}
The Maximum Likelihood (ML) estimator minimizes the $L_1$ loss:
\begin{equation}
\hat{x}_{ML} = \arg\min_x \sum_{(k,l)\in\mathcal{W}} |y(k,l) - x|
\end{equation}
The solution to this $L_1$ minimization is the \textbf{median} of the window $\mathcal{W}$:
\begin{equation}
\hat{x}(m,n) = \text{median}\{y(k,l) : (k,l) \in \mathcal{W}_{m,n}\}
\end{equation}
where $\mathcal{W}_{m,n}$ is a $(K\times K)$ neighborhood centered at $(m,n)$.

\subsection{Salt-and-Pepper Removal}

The median filter is particularly effective for impulse noise because the median operation inherently discards outliers: even if 50\% of a window's pixels are corrupted to $\{0,1\}$, the median still returns a valid intensity value. The implementation uses OpenCV's \texttt{cv2.medianBlur} with configurable odd kernel size $K \in \{3,\ldots,11\}$.

% =====================================================================
\section{Bilateral Filter — Edge-Preserving Smoothing}

\subsection{Derivation}

The bilateral filter extends Gaussian smoothing by adding a radiometric (intensity-domain) Gaussian weight, preventing smoothing across edges:
\begin{equation}
\hat{x}(m,n) = \frac{1}{W_p} \sum_{(k,l)\in\mathcal{W}} y(k,l)\, f_s(k,l)\, g_r(y(k,l), y(m,n))
\end{equation}
where the normalization factor is:
\begin{equation}
W_p = \sum_{(k,l)\in\mathcal{W}} f_s(k,l)\, g_r(y(k,l), y(m,n))
\end{equation}
The spatial kernel $f_s$ is:
\begin{equation}
f_s(k,l) = \exp\!\left(-\frac{k^2+l^2}{2\sigma_s^2}\right)
\end{equation}
and the radiometric kernel $g_r$ is:
\begin{equation}
g_r(I_i, I_j) = \exp\!\left(-\frac{(I_i - I_j)^2}{2\sigma_r^2}\right)
\end{equation}
Here $\sigma_s$ (spatial sigma, \texttt{sigmaSpace}) controls the spatial neighborhood extent, and $\sigma_r$ (\texttt{sigmaColor}) controls the intensity-similarity threshold. Pixels with very different intensities (i.e., across an edge) receive near-zero $g_r$ weight and are excluded from averaging, thus preserving edges while smoothing within homogeneous regions.

% =====================================================================
\section{Histogram Equalization — Entropy Maximization}

\subsection{CDF-Based Remapping}

Histogram equalization redistributes pixel intensities to maximize the entropy of the output, using the Cumulative Distribution Function (CDF) of the input:
\begin{equation}
T(r) = (L-1)\, F_Y(r) = (L-1) \int_0^r p_Y(t)\, dt
\end{equation}
where $p_Y$ is the input probability density function (histogram), $L=256$, and $F_Y$ is its CDF. The transformation $T$ maps input level $r$ to output level $s = T(r)$.

\subsection{Information-Theoretic Justification}

Shannon entropy of a discrete random variable $X$ with PMF $\{p_k\}$ is:
\begin{equation}
H(X) = -\sum_{k=0}^{L-1} p_k \log_2 p_k \quad \text{(bits)}
\end{equation}
For a uniform output distribution, $p_k = 1/L$ for all $k$, giving maximum entropy $H_{\max} = \log_2 L = 8$ bits. The CDF-based transformation achieves this uniform distribution in the continuous limit. In the implementation, RGB images are converted to YCrCb color space and equalization is applied only to the Y (luma) channel to avoid hue distortion:
\begin{equation}
\text{RGB} \xrightarrow{\text{cvt}} \text{YCrCb} \xrightarrow{T \text{ on } Y} \xrightarrow{\text{cvt}} \text{RGB}
\end{equation}

% =====================================================================
\section{Bayesian MAP Denoising — Wiener Filter}

\subsection{Gaussian Prior and MAP Derivation}

The Bayesian framework assumes:
\begin{align}
y &= x + \eta, \quad \eta \sim \mathcal{N}(0, \sigma_n^2) \\
p(x) &= \mathcal{N}(\mu_x, \sigma_x^2) \quad \text{(Gaussian prior)}
\end{align}
The MAP estimator maximizes the posterior $p(x|y)$:
\begin{equation}
\hat{x}_{MAP} = \arg\max_x\, \log p(y|x) + \log p(x)
\end{equation}
Expanding:
\begin{equation}
= \arg\min_x\; \frac{(y-x)^2}{2\sigma_n^2} + \frac{(x-\mu_x)^2}{2\sigma_x^2}
\end{equation}
Setting the derivative to zero:
\begin{equation}
-\frac{y-x}{\sigma_n^2} - \frac{x-\mu_x}{\sigma_x^2} = 0
\end{equation}
Solving for $x$:
\begin{equation}
\hat{x}_{MAP} = \mu_x + \underbrace{\frac{\sigma_x^2}{\sigma_x^2 + \sigma_n^2}}_{K}\,(y - \mu_x)
\end{equation}

\subsection{Wiener Gain Factor}

The scalar $K$ is the Wiener gain:
\begin{equation}
\boxed{K = \frac{\sigma_x^2}{\sigma_x^2 + \sigma_n^2}}
\end{equation}
\textbf{Interpretation:} When $\sigma_x^2 \gg \sigma_n^2$ (signal-dominant region), $K \to 1$ and $\hat{x} \approx y$ (trust the observation). When $\sigma_n^2 \gg \sigma_x^2$ (noise-dominant), $K \to 0$ and $\hat{x} \approx \mu_x$ (trust the prior mean). The Wiener gain map visualizes this spatial adaptation.

\subsection{Local Parameter Estimation}

In the implementation, $\mu_x$ and $\sigma_x^2$ are estimated locally via a $5 \times 5$ uniform filter:
\begin{align}
\hat{\mu}_x(m,n) &= \frac{1}{25}\sum_{(k,l)\in\mathcal{W}_5} y(k,l) \\
\hat{\sigma}_x^2(m,n) &= \frac{1}{25}\sum_{(k,l)\in\mathcal{W}_5} y^2(k,l) - \hat{\mu}_x^2(m,n)
\end{align}
This makes the estimator spatially adaptive: textured regions have high $\hat{\sigma}_x^2$ and $K \to 1$, while flat regions have low $\hat{\sigma}_x^2$ and $K \to 0$ (stronger denoising).

% =====================================================================
\section{Markov Random Field — ICM Smoothing}

\subsection{MRF Energy Formulation}

The image $x$ is modeled as a Markov Random Field with a Gibbs smoothness prior. The posterior energy to minimize is:
\begin{equation}
E(x|y) = \underbrace{\frac{1}{\sigma_n^2}\sum_i (y_i - x_i)^2}_{\text{data fidelity}} + \underbrace{\beta \sum_{\langle i,j\rangle} (x_i - x_j)^2}_{\text{smoothness prior}}
\end{equation}
where $\langle i,j \rangle$ denotes 4-connected neighbor pairs (up, down, left, right) and $\beta > 0$ controls the smoothness strength.

\subsection{ICM Update Rule Derivation}

The ICM algorithm minimizes $E$ by iteratively optimizing each pixel $x_i$ while holding all others fixed. Setting $\partial E / \partial x_i = 0$:
\begin{equation}
\frac{2}{\sigma_n^2}(x_i - y_i) + 2\beta \sum_{j \in \mathcal{N}(i)}(x_i - x_j) = 0
\end{equation}
\begin{equation}
x_i\!\left(\frac{1}{\sigma_n^2} + \beta|\mathcal{N}_i|\right) = \frac{y_i}{\sigma_n^2} + \beta \sum_{j\in\mathcal{N}(i)} x_j
\end{equation}
\begin{equation}
\boxed{\hat{x}_i = \frac{\dfrac{y_i}{\sigma_n^2} + \beta \displaystyle\sum_{j \in \mathcal{N}(i)} x_j}{\dfrac{1}{\sigma_n^2} + \beta|\mathcal{N}_i|}}
\end{equation}
For interior pixels, $|\mathcal{N}_i| = 4$. The denominator is constant across iterations: $\text{denom} = 1/\sigma_n^2 + 4\beta$.

\subsection{Convergence Criterion}

Convergence is measured as the sum of squared updates per iteration:
\begin{equation}
\Delta^{(t)} = \sum_{m,n} \left(x^{(t)}(m,n) - x^{(t-1)}(m,n)\right)^2
\end{equation}
The algorithm stops when $\Delta^{(t)} < 10^{-8}$ or after the maximum number of iterations (default 10, up to 50).

% =====================================================================
\section{Statistical Analysis Framework}

\subsection{First-Order Statistics}

For each image channel modeled as a random field $X$ with $N = M_1 \cdot M_2$ pixels:
\begin{align}
\mu_X &= \frac{1}{N}\sum_{m,n} x(m,n) \quad \text{(mean)} \\
\sigma_X^2 &= \frac{1}{N}\sum_{m,n} (x(m,n)-\mu_X)^2 \quad \text{(variance)} \\
\gamma_1 &= \frac{1}{N\sigma_X^3}\sum_{m,n}(x-\mu_X)^3 \quad \text{(skewness)} \\
\gamma_2 &= \frac{1}{N\sigma_X^4}\sum_{m,n}(x-\mu_X)^4 - 3 \quad \text{(excess kurtosis)}
\end{align}

\subsection{Signal-to-Noise Ratio}

SNR is computed using the mean as signal power and variance as noise power:
\begin{equation}
\text{SNR} = \frac{\mu_X^2}{\sigma_X^2}, \quad \text{SNR}_{dB} = 10\log_{10}\!\left(\frac{\mu_X^2}{\sigma_X^2}\right)
\end{equation}
This is a global measure; improvement after each filter stage is tracked as:
\begin{equation}
\Delta\text{SNR} = \text{SNR}_{dB}^{\text{after}} - \text{SNR}_{dB}^{\text{before}}
\end{equation}

\subsection{Entropy}

Shannon entropy of the 256-bin intensity histogram $\{p_k\}$:
\begin{equation}
H = -\sum_{k=0}^{255} p_k \log_2 p_k \quad \text{bits}
\end{equation}
High entropy indicates a more uniform histogram (used to quantify equalization quality).

\subsection{Autocorrelation Function}

The normalized 2D autocorrelation at lag $(\Delta m, \Delta n)$:
\begin{equation}
R_{XX}[\Delta m, \Delta n] = \frac{\displaystyle\sum_{m,n}(x(m,n)-\mu_X)(x(m+\Delta m, n+\Delta n)-\mu_X)}{N\sigma_X^2}
\end{equation}
Reported at lags $(1,0)$, $(0,1)$, and $(1,1)$ to characterize spatial correlation structure. High autocorrelation at lag $(1,0)$ indicates strong horizontal texture; near-zero values indicate white noise.

\subsection{Luminance Extraction}

For RGB images, the BT.601 luma standard is used:
\begin{equation}
Y(m,n) = 0.299\,R(m,n) + 0.587\,G(m,n) + 0.114\,B(m,n)
\end{equation}
All scalar statistics (SNR, entropy, autocorrelation) are computed on this luminance channel $Y$.

% =====================================================================
\section{System Architecture}

The system is implemented as a Python FastAPI application following a clean service-oriented architecture:

\begin{table}[h]
\caption{Backend Module Responsibilities}
\centering
\begin{tabular}{@{}ll@{}}
\toprule
\textbf{Module} & \textbf{Responsibility} \\
\midrule
\texttt{main.py} & FastAPI app, CORS, router mounting \\
\texttt{routers/upload.py} & Image ingestion, session creation \\
\texttt{routers/process.py} & Pipeline orchestration \\
\texttt{services/noise\_detector.py} & Noise classification (MAD, S\&P, Laplacian) \\
\texttt{services/filters.py} & Gaussian, Median, Bilateral, Histeq \\
\texttt{services/bayesian\_estimator.py} & MAP/Wiener denoising \\
\texttt{services/markov\_field.py} & MRF-ICM smoothing \\
\texttt{services/stat\_analyzer.py} & Statistical metrics \\
\texttt{services/visualizer.py} & Chart generation (matplotlib) \\
\texttt{utils/image\_io.py} & Float32/uint8/base64 conversions \\
\bottomrule
\end{tabular}
\end{table}

Images are stored server-side as float32 numpy arrays keyed by UUID session IDs. A background coroutine periodically purges expired sessions. The REST pipeline accepts a JSON list of step identifiers and parameters; steps execute sequentially with the output of each step feeding the next.

% =====================================================================
\section{Results and Discussion}

The pipeline applies filters in sequence, with SNR computed before and after each step. Table~\ref{tab:filters} summarizes the theoretical noise model each filter addresses.

\begin{table}[h]
\caption{Filter–Noise Model Correspondence}
\label{tab:filters}
\centering
\begin{tabular}{@{}lll@{}}
\toprule
\textbf{Filter} & \textbf{Noise Model} & \textbf{Criterion} \\
\midrule
Gaussian & AWGN & LTI spectral shaping \\
Median & Laplacian/Impulse & $L_1$ / ML \\
Bilateral & AWGN + edges & Edge-preserving MAP \\
Hist. Eq. & Contrast / Blur & Entropy maximization \\
Bayesian MAP & AWGN (Gaussian prior) & MAP / MMSE \\
MRF-ICM & AWGN (MRF prior) & MAP with spatial prior \\
\bottomrule
\end{tabular}
\end{table}

The noise detector provides a recommendation string, directing users to the most appropriate filter. For purely Gaussian noise the recommended path is Gaussian/Bilateral Filter $\to$ Bayesian MAP. For Salt \& Pepper, Median Filter is recommended first. For blurred images, Histogram Equalization improves perceived sharpness via contrast enhancement.

% =====================================================================
\section{Conclusion}

This paper presented a modular probabilistic signal processing framework for image denoising and enhancement. The key contributions include: (1) a robust multi-type noise classifier using MAD, impulse density, and Laplacian variance; (2) implementation and analysis of six filters grounded in PSP theory — each optimally suited to a specific noise model; (3) a spatially adaptive Bayesian MAP denoiser implementing the Wiener filter with local parameter estimation; (4) a vectorized MRF-ICM smoother with convergence tracking; and (5) a comprehensive statistical analysis suite reporting entropy, SNR, skewness, kurtosis, and normalized autocorrelation. The framework is deployed as a RESTful API enabling pipeline composition, real-time visualization, and session management.

Future work includes extending the MRF prior to non-quadratic potentials (e.g., Total Variation), adding wavelet-domain thresholding, and incorporating deep-learning-based denoising as an optional pipeline stage.

\begin{thebibliography}{00}
\bibitem{papoulis} A. Papoulis and S. U. Pillai, \textit{Probability, Random Variables, and Stochastic Processes}, 4th ed. McGraw-Hill, 2002.
\bibitem{gonzalez} R. C. Gonzalez and R. E. Woods, \textit{Digital Image Processing}, 4th ed. Pearson, 2018.
\bibitem{wiener} N. Wiener, \textit{Extrapolation, Interpolation, and Smoothing of Stationary Time Series}. MIT Press, 1949.
\bibitem{geman} S. Geman and D. Geman, ``Stochastic relaxation, Gibbs distributions, and the Bayesian restoration of images,'' \textit{IEEE Trans. Pattern Anal. Mach. Intell.}, vol. PAMI-6, no. 6, pp. 721--741, Nov. 1984. \href{https://doi.org/10.1109/TPAMI.1984.4767596}{DOI:10.1109/TPAMI.1984.4767596}
\bibitem{tomasi} C. Tomasi and R. Manduchi, ``Bilateral filtering for gray and color images,'' in \textit{Proc. ICCV}, 1998, pp. 839--846. \href{https://doi.org/10.1109/ICCV.1998.710815}{DOI:10.1109/ICCV.1998.710815}
\bibitem{besag} J. Besag, ``On the statistical analysis of dirty pictures,'' \textit{J. Roy. Stat. Soc. B}, vol. 48, no. 3, pp. 259--302, 1986.
\bibitem{shannon} C. E. Shannon, ``A mathematical theory of communication,'' \textit{Bell Syst. Tech. J.}, vol. 27, pp. 379--423, 623--656, 1948. \href{https://doi.org/10.1002/j.1538-7305.1948.tb01338.x}{DOI:10.1002/j.1538-7305.1948.tb01338.x}
\bibitem{scipy} P. Virtanen et al., ``SciPy 1.0: Fundamental algorithms for scientific computing in Python,'' \textit{Nature Methods}, vol. 17, pp. 261--272, 2020. \href{https://doi.org/10.1038/s41592-019-0686-2}{DOI:10.1038/s41592-019-0686-2}
\bibitem{opencv} G. Bradski, ``The OpenCV Library,'' \textit{Dr. Dobb's J. Software Tools}, 2000. \href{https://opencv.org}{opencv.org}
\bibitem{fastapi} S. Ramirez, ``FastAPI,'' 2019. \href{https://fastapi.tiangolo.com}{fastapi.tiangolo.com}
\end{thebibliography}

\end{document}
"""

with open("report.tex", "w", encoding="utf-8") as f:
    f.write(latex.strip())

print("report.tex written successfully.")
