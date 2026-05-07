p1 = r"""
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
\usepackage{multirow}

\begin{document}

\title{Intelligent Image Noise Filtering and Statistical Analysis:\\A Probabilistic Signal Processing Framework}

\author{
\IEEEauthorblockN{Aryan Singh \quad Abhishek Singh \quad Anuj Karandikar}
\IEEEauthorblockA{
\textit{Department of Electronics \& Communication Engineering}\\
UID: 2024200119 \quad UID: 2024200120 \quad UID: 2024200051
}
}

\maketitle

\begin{abstract}
This paper presents a comprehensive probabilistic signal processing (PSP) framework for digital image noise characterization and removal. Noise in digital imagery arises from multiple physical sources including photon shot noise, thermal sensor noise, quantization errors, and transmission channel corruption. Addressing these requires both a robust noise identification mechanism and a suite of mathematically grounded filters, each optimal under a specific noise model. The proposed system implements an eight-stage processing pipeline: noise classification via the Median Absolute Deviation (MAD) estimator and Laplacian variance; Gaussian filtering as a Linear Time-Invariant (LTI) spectral shaper; Median filtering as the Maximum Likelihood estimator under the Laplacian distribution; Bilateral filtering for edge-preserving spatial-radiometric smoothing; Histogram Equalization for entropy maximization via CDF remapping; Bayesian Maximum A Posteriori (MAP) denoising through a spatially adaptive pixelwise Wiener filter; and Markov Random Field (MRF) regularization via Iterated Conditional Modes (ICM). The system is deployed as a RESTful API using FastAPI, with session-based image management and per-step SNR tracking. Statistical analysis reports entropy, skewness, excess kurtosis, and normalized 2-D autocorrelation at each pipeline stage. Experimental evaluation confirms consistent SNR improvement across all noise categories tested.
\end{abstract}

\begin{IEEEkeywords}
noise filtering, Bayesian MAP estimation, Wiener filter, Markov Random Field, bilateral filter, histogram equalization, signal-to-noise ratio, probabilistic signal processing, FastAPI, image restoration
\end{IEEEkeywords}

\section{Introduction}

\subsection{Motivation and Background}
Digital images are the primary modality for information in medical diagnostics, remote sensing, surveillance, and consumer photography. Every image acquisition chain --- from photon absorption at the sensor to analog-to-digital conversion --- introduces stochastic perturbations collectively termed \textit{image noise}. The design of filters that remove noise while preserving clinically or visually relevant structure is therefore a fundamental problem in signal processing.

Classical deterministic filters such as box filters treat all spatial locations equivalently, leading to edge blurring. Modern approaches model both the image and the noise as random processes and derive estimators that are optimal in a well-defined statistical sense. This paper documents one such system, implemented as a production-grade Python backend, covering the theoretical derivation, practical implementation, and quantitative evaluation of six distinct filtering algorithms.

\subsection{Probabilistic Signal Processing Framework}
In the PSP framework an image $\mathbf{x} \in \mathbb{R}^{M \times N}$ is modeled as a realization of a 2-D random field $X(m,n)$ with joint probability density $p_X$. The observed noisy image is:
\begin{equation}
Y(m,n) = X(m,n) + \eta(m,n)
\label{eq:model}
\end{equation}
where $\eta$ is an independent noise process. Filtering is then estimation: find $\hat{X}$ that minimizes a risk functional under the posterior distribution $p(X|Y)$.

Three common risk criteria yield three classic estimators:
\begin{align}
\hat{x}_{MMSE} &= \mathbb{E}[X|Y] \quad (L_2 \text{ risk}) \\
\hat{x}_{MAP}  &= \arg\max_x\, p(X|Y) \quad (0\text{-}1 \text{ risk}) \\
\hat{x}_{MAE}  &= \text{median}[p(X|Y)] \quad (L_1 \text{ risk})
\end{align}
Under a Gaussian prior the MMSE and MAP solutions coincide with the Wiener filter. Under a Laplacian prior, the MAE solution is the median filter.

\subsection{System Contributions}
The key contributions of this work are:
\begin{itemize}
\item A three-feature noise classifier (MAD, impulse density, Laplacian variance) that jointly detects Gaussian, Salt-and-Pepper, and blur degradations.
\item Rigorous derivation of all six filter algorithms from their underlying probabilistic models.
\item A spatially-adaptive Bayesian MAP denoiser with per-pixel Wiener gain visualization.
\item A vectorized MRF-ICM implementation with convergence energy tracking.
\item A full statistical report (entropy, SNR, kurtosis, autocorrelation) generated at each pipeline step.
\item A RESTful FastAPI service with UUID session management enabling stateful multi-step pipelines.
\end{itemize}

\section{Noise Modeling and Detection}

\subsection{Taxonomy of Image Noise}
Three noise types are addressed in this system:

\textbf{Additive White Gaussian Noise (AWGN):} Arises from thermal (Johnson-Nyquist) noise in the sensor readout circuit. Characterized by:
\begin{equation}
\eta(m,n) \overset{iid}{\sim} \mathcal{N}(0,\sigma_n^2)
\end{equation}
The Power Spectral Density (PSD) is flat: $S_\eta(u,v) = \sigma_n^2$ for all frequencies --- hence ``white''.

\textbf{Salt-and-Pepper (Impulse) Noise:} Caused by faulty sensor pixels or transmission bit errors. Each pixel is independently corrupted with probability $\rho$:
\begin{equation}
Y(m,n) = \begin{cases} 0 & \text{with prob. } \rho/2 \\ 1 & \text{with prob. } \rho/2 \\ X(m,n) & \text{with prob. } 1-\rho \end{cases}
\end{equation}

\textbf{Blur:} Results from defocus, motion, or excessive low-pass filtering, and is characterized by loss of high-frequency energy (low Laplacian variance).

\subsection{Gaussian Noise Estimation: MAD Estimator}

A pre-filtering step isolates the high-frequency residual:
\begin{equation}
R(m,n) = Y(m,n) - \tilde{Y}(m,n)
\end{equation}
where $\tilde{Y}$ is the Gaussian-smoothed image ($\sigma = 1.5$). For pure AWGN, $R \approx \eta$. The robust standard deviation estimate uses:
\begin{equation}
\hat{\sigma}_n = \frac{\mathrm{median}_{m,n}\bigl(|R(m,n)|\bigr)}{0.6745}
\label{eq:mad}
\end{equation}
\textit{Derivation of 0.6745:} If $R \sim \mathcal{N}(0,\sigma^2)$ then $|R|$ follows a half-normal distribution. The median of $|R|$ satisfies:
\begin{equation}
F_{|R|}\!\left(\tilde{r}\right) = 0.5 \implies \tilde{r} = \sigma\,\Phi^{-1}(0.75) = 0.6745\,\sigma
\end{equation}
where $\Phi^{-1}$ is the inverse standard normal CDF. Rearranging gives \eqref{eq:mad}. The MAD estimator achieves 50\% breakdown point, meaning it remains accurate even when up to 50\% of samples are outliers (S\&P pixels).

\subsection{Salt-and-Pepper Detection}
The impulse density is estimated by counting pixels at saturation boundaries:
\begin{equation}
\hat{\rho} = \frac{\#\{(m,n):\, Y(m,n) < 0.02\;\cup\; Y(m,n) > 0.98\}}{M \cdot N}
\end{equation}
A threshold of $\hat{\rho} > 0.005$ flags Salt \& Pepper noise.

\subsection{Blur Detection via Laplacian Variance}
The discrete 2-D Laplacian operator:
\begin{equation}
(\nabla^2 Y)(m,n) = Y(m{+}1,n) + Y(m{-}1,n) + Y(m,n{+}1) + Y(m,n{-}1) - 4Y(m,n)
\end{equation}
responds strongly to edges and texture. Its variance across the image measures overall sharpness:
\begin{equation}
V_L = \mathrm{Var}\bigl[\nabla^2 Y\bigr]
\end{equation}
Images with $V_L < 50$ (on the uint8 scale) are classified as blurred, as blur suppresses the high-frequency energy that the Laplacian detects.

\subsection{Automatic Filter Recommendation}
Based on detected noise type, the system constructs a recommendation string:
\begin{itemize}
\item S\&P detected $\rightarrow$ Median Filter (optimal ML under Laplacian)
\item Gaussian detected $\rightarrow$ Gaussian / Bilateral / Bayesian MAP
\item Blur detected $\rightarrow$ Histogram Equalization (contrast enhancement)
\end{itemize}

\section{Gaussian Filter: LTI System Analysis}

\subsection{Impulse Response and Convolution}
The 2-D Gaussian kernel with scale $\sigma$ is:
\begin{equation}
h(m,n;\sigma) = \frac{1}{2\pi\sigma^2}\exp\!\left(-\frac{m^2+n^2}{2\sigma^2}\right)
\end{equation}
The filtered image is the 2-D discrete convolution:
\begin{equation}
\hat{X}(m,n) = (h * Y)(m,n) = \sum_{k=-\infty}^{\infty}\sum_{l=-\infty}^{\infty} h(k,l)\,Y(m-k,n-l)
\end{equation}
Because $h$ does not depend on $(m,n)$, this is a \emph{Linear Time-Invariant} (spatially invariant) system.

\subsection{Frequency-Domain Analysis}
Taking the 2-D Fourier transform $\mathcal{F}\{h\}$:
\begin{equation}
H(u,v) = \exp\!\left(-2\pi^2\sigma^2(u^2+v^2)\right)
\end{equation}
The filter has unit DC gain ($H(0,0)=1$) and falls off as a Gaussian in the frequency domain with bandwidth $B = 1/(2\pi\sigma)$.

\subsection{Output PSD and Noise Attenuation}
For a LTI system, the output PSD equals:
\begin{equation}
S_{\hat{X}}(u,v) = |H(u,v)|^2 \cdot S_Y(u,v)
\end{equation}
Since $S_Y = S_X + S_\eta$ (independent noise), the output noise PSD is:
\begin{equation}
S_{\eta,\text{out}}(u,v) = |H(u,v)|^2 \cdot \sigma_n^2 = \sigma_n^2 \exp\!\left(-4\pi^2\sigma^2(u^2+v^2)\right)
\end{equation}
Total output noise power:
\begin{equation}
\sigma_{\eta,\text{out}}^2 = \sigma_n^2 \int\!\!\int |H|^2\,du\,dv = \frac{\sigma_n^2}{4\pi\sigma^2}
\end{equation}
Thus the Gaussian filter reduces noise variance by a factor of $4\pi\sigma^2$, at the cost of blurring signal components at the same high frequencies.

\subsection{Implementation}
The implementation uses \texttt{scipy.ndimage.gaussian\_filter} applied independently per channel, with the image clamped to $[0,1]$ in float32. Parameter: $\sigma \in [0.5, 5.0]$.

\section{Median Filter: Optimal ML Estimator}

\subsection{Laplacian Noise Model}
The Laplacian (double-exponential) distribution models impulse-like noise:
\begin{equation}
p(\eta;\,b) = \frac{1}{2b}\exp\!\left(-\frac{|\eta|}{b}\right), \quad \sigma_\eta^2 = 2b^2
\end{equation}

\subsection{ML Derivation}
Given i.i.d. observations $\{y_k\}_{k=1}^{K}$ in a window centered at $(m,n)$, the log-likelihood under the Laplacian model is:
\begin{equation}
\ell(x) = \sum_{k=1}^{K} \log p(y_k - x) = -K\log(2b) - \frac{1}{b}\sum_{k=1}^{K}|y_k - x|
\end{equation}
Maximizing $\ell$ is equivalent to minimizing the $L_1$ loss:
\begin{equation}
\hat{x}_{ML} = \arg\min_{x \in \mathbb{R}} \sum_{k=1}^{K} |y_k - x|
\label{eq:l1}
\end{equation}
The solution to \eqref{eq:l1} is the \textbf{sample median}:
\begin{equation}
\hat{x}_{ML}(m,n) = \mathrm{median}\{y_k : (k,l) \in \mathcal{W}_{m,n}\}
\end{equation}

\subsection{Robustness to Impulse Noise}
The median has a \emph{breakdown point} of $\lfloor K/2 \rfloor / K \approx 50\%$: the estimate remains bounded even if nearly half the window is corrupted. In contrast, the mean has a 0\% breakdown point (a single extreme value can arbitrarily distort the estimate). This makes the median filter the preferred choice for Salt \& Pepper noise.

\subsection{Implementation Details}
OpenCV's \texttt{cv2.medianBlur} is used for efficiency (optimized for uint8 images). The pipeline converts float32 $\to$ uint8 before filtering and back to float32 after. Odd kernel sizes $K \in \{3, 5, 7, 9, 11\}$ are supported; even values are automatically incremented to the next odd integer.
"""
with open("report.tex","w",encoding="utf-8") as f:
    f.write(p1.strip())
print("Part 1 written.")
