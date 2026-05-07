p2 = r"""
\section{Bilateral Filter: Edge-Preserving Smoothing}

\subsection{Motivation}
The Gaussian filter treats all pixels within the spatial kernel equally, blurring edges. The bilateral filter adds a second, \emph{radiometric} (intensity-domain) Gaussian that downweights contributions from pixels with very different intensities, effectively preserving edges while smoothing within homogeneous regions.

\subsection{Filter Definition}
\begin{equation}
\hat{X}(m,n) = \frac{1}{W(m,n)}\sum_{(k,l)\in\mathcal{W}} Y(k,l)\,f_s(m,n,k,l)\,g_r(Y(m,n),Y(k,l))
\end{equation}
with normalization:
\begin{equation}
W(m,n) = \sum_{(k,l)\in\mathcal{W}} f_s(m,n,k,l)\,g_r(Y(m,n),Y(k,l))
\end{equation}
The spatial kernel is:
\begin{equation}
f_s(m,n,k,l) = \exp\!\left(-\frac{(m-k)^2+(n-l)^2}{2\sigma_s^2}\right)
\end{equation}
The radiometric kernel is:
\begin{equation}
g_r(I_p, I_q) = \exp\!\left(-\frac{(I_p - I_q)^2}{2\sigma_r^2}\right)
\end{equation}

\subsection{Interpretation of Parameters}
\begin{itemize}
\item $\sigma_s$ (\texttt{sigmaSpace}): Controls the spatial extent of smoothing. Larger $\sigma_s$ averages over a wider neighborhood.
\item $\sigma_r$ (\texttt{sigmaColor}): Controls intensity selectivity. Small $\sigma_r$ (e.g., 10) only averages pixels with very similar intensities (strong edge preservation). Large $\sigma_r$ (e.g., 150) approaches standard Gaussian smoothing.
\item $d$ (\texttt{diameter}): Diameter of the pixel neighborhood considered; set to $d = 9$ by default.
\end{itemize}

\subsection{Edge Preservation Property}
At a step edge where $|I_p - I_q| \gg \sigma_r$, $g_r \approx 0$, so those cross-edge pixels contribute negligibly. The effective local kernel on the smooth side of the edge becomes:
\begin{equation}
w_\text{eff}(k,l) \propto f_s(k,l) \cdot \mathbf{1}[|I_{kl}-I_{mn}| \ll \sigma_r]
\end{equation}
This makes the bilateral filter a locally adaptive, nonlinear filter. It does not have a simple frequency-domain representation.

\subsection{Implementation Note}
The implementation applies \texttt{cv2.bilateralFilter} per channel on uint8 images. Images larger than $2000 \times 2000$ pixels are rejected to prevent excessive computation time (bilateral filtering is $O(K^2 MN)$ per iteration, non-separable).

\section{Histogram Equalization: Entropy Maximization}

\subsection{CDF-Based Intensity Remapping}
Let $p_Y(r)$ be the normalized intensity histogram (empirical PMF) of the input image, and $F_Y(r) = \sum_{t=0}^{r} p_Y(t)$ its CDF. The equalization transform is:
\begin{equation}
T(r) = (L-1)\,F_Y(r), \quad L = 256
\end{equation}
Applied pixelwise: $s(m,n) = T(Y(m,n))$.

\subsection{Proof of Entropy Maximization}
For a continuous random variable $Y$ with PDF $p_Y$, a monotone transform $s = T(y)$ induces output PDF:
\begin{equation}
p_S(s) = p_Y(T^{-1}(s))\left|\frac{dT^{-1}}{ds}\right| = p_Y(y)\left|\frac{dy}{ds}\right|
\end{equation}
Setting $T'(y) = (L-1)\,p_Y(y)$ (i.e., $T = (L-1)F_Y$):
\begin{equation}
p_S(s) = p_Y(y) \cdot \frac{1}{(L-1)\,p_Y(y)} = \frac{1}{L-1}
\end{equation}
The output distribution is uniform on $[0, L-1]$, achieving maximum Shannon entropy:
\begin{equation}
H_{\max} = \log_2(L) = \log_2(256) = 8 \text{ bits}
\end{equation}
This is the theoretical upper bound for an 8-bit image, and histogram equalization achieves it in the continuous limit.

\subsection{Color Image Handling}
Applying equalization independently on R, G, B channels distorts the hue (color ratios change). Instead the implementation converts to YCrCb color space:
\begin{equation}
\begin{bmatrix}Y\\C_r\\C_b\end{bmatrix} = \begin{bmatrix}0.299&0.587&0.114\\0.5&-0.4187&-0.0813\\-0.1687&-0.3313&0.5\end{bmatrix}\begin{bmatrix}R\\G\\B\end{bmatrix} + \begin{bmatrix}0\\128\\128\end{bmatrix}
\end{equation}
Equalization is applied only to the luminance channel $Y$. Chrominance channels $C_r, C_b$ are unchanged, preserving color fidelity. The image is then converted back to RGB.

\section{Bayesian MAP Denoising: Wiener Filter}

\subsection{Statistical Model}
The observation model is (from \eqref{eq:model}):
\begin{align}
Y | X &\sim \mathcal{N}(X,\, \sigma_n^2) \quad \text{(likelihood)}\\
X &\sim \mathcal{N}(\mu_x,\, \sigma_x^2) \quad \text{(Gaussian prior)}
\end{align}

\subsection{Full MAP Derivation}
The posterior is also Gaussian (conjugate prior):
\begin{equation}
p(X|Y) \propto p(Y|X)\,p(X) = \mathcal{N}(X;\,Y,\sigma_n^2)\cdot\mathcal{N}(X;\,\mu_x,\sigma_x^2)
\end{equation}
Taking the log and expanding:
\begin{equation}
\log p(X|Y) = -\frac{(Y-X)^2}{2\sigma_n^2} - \frac{(X-\mu_x)^2}{2\sigma_x^2} + \text{const}
\end{equation}
Differentiating with respect to $X$ and setting to zero:
\begin{equation}
\frac{Y - \hat{X}}{\sigma_n^2} - \frac{\hat{X} - \mu_x}{\sigma_x^2} = 0
\end{equation}
Solving:
\begin{equation}
\hat{X}_{MAP} = \frac{\sigma_x^2\, Y + \sigma_n^2\,\mu_x}{\sigma_x^2 + \sigma_n^2}
= \mu_x + \underbrace{\frac{\sigma_x^2}{\sigma_x^2 + \sigma_n^2}}_{K}(Y - \mu_x)
\label{eq:wiener}
\end{equation}

\subsection{Wiener Gain Interpretation}
The scalar $K$ in \eqref{eq:wiener} is the \textbf{Wiener gain}:
\begin{equation}
\boxed{K = \frac{\sigma_x^2}{\sigma_x^2 + \sigma_n^2} \in [0,1]}
\end{equation}
It interpolates between the prior mean $\mu_x$ (when $K=0$, noise-dominated) and the noisy observation $Y$ (when $K=1$, signal-dominated). The posterior variance is:
\begin{equation}
\mathrm{Var}[X|Y] = \frac{\sigma_x^2\,\sigma_n^2}{\sigma_x^2 + \sigma_n^2} = K\,\sigma_n^2
\end{equation}
Note $\hat{X}_{MAP} = \hat{X}_{MMSE}$ under the Gaussian prior, so this estimator simultaneously minimizes both $L_2$ risk (MMSE) and achieves the MAP.

\subsection{Local Parameter Estimation}
In practice $\mu_x$ and $\sigma_x^2$ are unknown and estimated locally using a $5\times5$ uniform window $\mathcal{W}_5$:
\begin{align}
\hat{\mu}_x(m,n) &= \frac{1}{25}\sum_{(k,l)\in\mathcal{W}_5} Y(k,l) \\
\hat{\sigma}_x^2(m,n) &= \max\!\left(0,\;\frac{1}{25}\sum_{(k,l)\in\mathcal{W}_5} Y(k,l)^2 - \hat{\mu}_x^2\right)
\end{align}
The $\max(0,\cdot)$ clamps negative values arising from floating-point round-off. This makes the denoiser \emph{spatially adaptive}: $K(m,n)$ is high in textured regions (preserve detail) and low in flat regions (aggressive denoising).

\subsection{Wiener Gain Map Visualization}
The system generates a false-color heatmap of $K(m,n)$ averaged over channels. Values near 0 (dark) indicate noise-dominated regions that are strongly smoothed; values near 1 (bright) indicate signal-dominated regions that are preserved.

\section{Markov Random Field: ICM Smoothing}

\subsection{MRF Definition}
An image $\mathbf{X}$ is a Markov Random Field with respect to a 4-connected neighborhood system $\mathcal{N}$ if for every pixel $i$:
\begin{equation}
p(X_i | X_{j \neq i}) = p(X_i | X_j,\, j \in \mathcal{N}(i))
\end{equation}
By the Hammersley-Clifford theorem, such an MRF has a Gibbs distribution:
\begin{equation}
p(\mathbf{X}) = \frac{1}{Z}\exp(-U(\mathbf{X}))
\end{equation}
where $U$ is the \emph{Gibbs energy} defined as a sum over clique potentials.

\subsection{Energy Function}
The MAP-MRF energy combines a data fidelity term (likelihood) and a smoothness prior (pairwise clique potentials):
\begin{equation}
E(\mathbf{x}|\mathbf{y}) = \underbrace{\frac{1}{\sigma_n^2}\sum_i (y_i - x_i)^2}_{\text{data fidelity}} + \underbrace{\beta \sum_{\langle i,j\rangle} (x_i - x_j)^2}_{\text{smoothness prior}}
\label{eq:mrf_energy}
\end{equation}
The quadratic pairwise potential $V(x_i,x_j) = (x_i-x_j)^2$ is a Gaussian MRF (GMRF) prior that penalizes intensity differences between neighboring pixels. Parameter $\beta \geq 0$ controls smoothness strength.

\subsection{ICM Update Rule Derivation}
The Iterated Conditional Modes algorithm minimizes \eqref{eq:mrf_energy} by optimizing one pixel at a time. For pixel $i$, the conditional energy is:
\begin{equation}
E(x_i | \mathbf{x}_{\setminus i}, \mathbf{y}) = \frac{(y_i-x_i)^2}{\sigma_n^2} + \beta\sum_{j\in\mathcal{N}(i)}(x_i-x_j)^2
\end{equation}
Setting $\partial E / \partial x_i = 0$:
\begin{equation}
-\frac{2(y_i-x_i)}{\sigma_n^2} + 2\beta\sum_{j\in\mathcal{N}(i)}(x_i-x_j) = 0
\end{equation}
Expanding the sum:
\begin{equation}
x_i\!\left(\frac{1}{\sigma_n^2} + \beta|\mathcal{N}_i|\right) = \frac{y_i}{\sigma_n^2} + \beta\sum_{j\in\mathcal{N}(i)} x_j
\end{equation}
\begin{equation}
\boxed{\hat{x}_i^{(t+1)} = \frac{y_i/\sigma_n^2 + \beta\displaystyle\sum_{j\in\mathcal{N}(i)} x_j^{(t)}}{1/\sigma_n^2 + \beta|\mathcal{N}_i|}}
\label{eq:icm_update}
\end{equation}
For interior pixels $|\mathcal{N}_i| = 4$, making the denominator a constant: $D = 1/\sigma_n^2 + 4\beta$.

\subsection{Vectorized Implementation}
Rather than iterating pixel by pixel, the neighbor sum in \eqref{eq:icm_update} is computed using a $3\times3$ uniform filter:
\begin{equation}
\sum_{j\in\mathcal{N}^*(i)} x_j = \texttt{uniform\_filter}(\mathbf{x},\,\text{size}=3) \times 9 - x_i
\end{equation}
where $\mathcal{N}^*(i)$ is the 8-connected neighborhood (includes diagonals in the vectorized approximation). This allows the entire image to be updated in a single vectorized pass per iteration, giving $O(MN)$ complexity per sweep.

\subsection{Convergence}
The convergence metric per iteration is:
\begin{equation}
\Delta^{(t)} = \left\|\mathbf{x}^{(t)} - \mathbf{x}^{(t-1)}\right\|_F^2 = \sum_{m,n}\bigl(x^{(t)}(m,n)-x^{(t-1)}(m,n)\bigr)^2
\end{equation}
The algorithm halts when $\Delta^{(t)} < 10^{-8}$ or after the maximum number of iterations (default 10, configurable up to 50). Since the energy \eqref{eq:mrf_energy} is strictly convex in $\mathbf{x}$, ICM converges to the global minimum.
"""
with open("report.tex","a",encoding="utf-8") as f:
    f.write("\n" + p2.strip())
print("Part 2 appended.")
