"""Locally generated chapter checks with exact answers and section coverage.

These are authored, parameterized exercises, not model output or copied textbook
questions. Their medium difficulty is a design label, not a calibrated score.
Each section has an explicit mathematical task; unsupported sections fail closed.
"""
from __future__ import annotations

import random
import sympy as sp


VERSION = "challenge-template-v1"


def exercise(label: str, a: int, b: int, language: str):
    """Return (stem, rule, substituted expression, exact answer)."""
    def pick(zh, en):
        return zh if language == "zh" else en

    def item(zh, en, rule_zh, rule_en, expression):
        return pick(zh, en), pick(rule_zh, rule_en), expression, sp.simplify(expression)

    A, B = sp.Integer(a), sp.Integer(b)
    cases = {
        '1.1': (f'物体的位置为 $s(t)={a}t^2+{b}t$。求 $t=1$ 到 $t=3$ 的平均速度。',
                f'Position is $s(t)={a}t^2+{b}t$. Find the average velocity from $t=1$ to $t=3$.',
                '平均速度等于位置变化除以时间变化。', 'Average velocity is displacement divided by elapsed time.', (A*9+B*3-(A+B))/2),
        '1.2': (f'用代数化简差商，求 $f(t)={a}t^2$ 在 $t={b}$ 处的瞬时变化率。',
                f'Simplify the difference quotient algebraically to find the instantaneous rate for $f(t)={a}t^2$ at $t={b}$.',
                '展开差商得到 $a(2t+h)$，再令 $h$ 趋于 0。', 'Expand the difference quotient to a(2t+h), then let h tend to zero.', 2*A*B),
        '1.3': (f'位置函数为 $s(t)={a}t^3+{b}t$，求 $t=2$ 时的瞬时速度。',
                f'Position is $s(t)={a}t^3+{b}t$. Find the instantaneous velocity at $t=2$.',
                '瞬时速度为位置函数的导数 $s\'(t)=3at^2+b$。', 'Instantaneous velocity is the derivative of position: s\'(t)=3at^2+b.', 12*A+B),
        '1.4': (f'圆周运动为 $x(t)={a}cos({b}t), y(t)={a}sin({b}t)$。求速率。',
                f'Circular motion has $x(t)={a}cos({b}t), y(t)={a}sin({b}t)$. Find the speed.',
                '分别求导，再计算 $sqrt((x\')^2+(y\')^2)$，利用 $sin^2+cos^2=1$。', 'Differentiate both coordinates and use speed=sqrt((x\')^2+(y\')^2) with sin²+cos²=1.', A*B),
        '1.5': (f'锐角 $theta$ 满足 $sin(theta)=3/5$。求 ${a}sin(2theta)$。',
                f'An acute angle theta satisfies $sin(theta)=3/5$. Find ${a}sin(2theta)$.',
                '锐角的余弦为正，由勾股恒等式得 $cos(theta)=4/5$，再用倍角公式。', 'The cosine is positive, so cos(theta)=4/5; then use the sine double-angle identity.', A*sp.Rational(24,25)),
        '1.6': (f'对 $y={a}sin(x)$ 在 $x_n=pi/2+2*pi*n$ 采样，其中 $n$ 为整数。所有采样点的纵坐标是多少？',
                f'Sample $y={a}sin(x)$ at $x_n=pi/2+2*pi*n$ for integer n. What is the common sampled y-value?',
                '采样相位相差整周期，因此所有采样值都等于 $a sin(pi/2)$。', 'The sample phases differ by whole periods, so every value equals a sin(pi/2).', A),
        '2.1': (f'用导数定义求 $f(x)={a}x^2+{b}$ 在 $x=3$ 处的导数。',
                f'Use the derivative definition for $f(x)={a}x^2+{b}$ to find f\'(3).',
                '先展开并约去差商中的 $h$，再令 $h$ 趋于 0，得到 $f\'(x)=2ax$。', 'Expand and cancel h in the difference quotient; its limit is f\'(x)=2ax.', 6*A),
        '2.2': (f'求 $f(x)={a}x^3+{b}x^2$ 在 $x=2$ 处的导数。',
                f'Find f\'(2) for $f(x)={a}x^3+{b}x^2$.',
                '逐项使用幂函数法则得到 $f\'(x)=3ax^2+2bx$。', 'Apply the power rule term by term: f\'(x)=3ax²+2bx.', 12*A+4*B),
        '2.3': (f'曲线 $y={a}x^2+{b}$ 在 $x=1$ 处的切线与纵轴相交。交点的纵坐标是多少？',
                f'The tangent to $y={a}x^2+{b}$ at x=1 meets the y-axis. Find its y-intercept.',
                '用 $y-f(1)=f\'(1)(x-1)$ 写切线方程，然后取 $x=0$。', 'Use y-f(1)=f\'(1)(x-1) for the tangent, then set x=0.', B-A),
        '2.4': (f'求 $f(x)={a}sin(x)+{b}cos(x)$ 的 $f\'(0)$。',
                f'Find f\'(0) for $f(x)={a}sin(x)+{b}cos(x)$.',
                '利用正弦与余弦的导数得到 $f\'(x)=a cos(x)-b sin(x)$。', 'Differentiate sine and cosine: f\'(x)=a cos(x)-b sin(x).', A),
        '2.5': (f'求 $f(x)=({a}x+{b})/(x+1)$ 的 $f\'(1)$。',
                f'Find f\'(1) for $f(x)=({a}x+{b})/(x+1)$.',
                '商法则给出 $f\'(x)=(a-b)/(x+1)^2$。', 'The quotient rule gives f\'(x)=(a-b)/(x+1)².', (A-B)/4),
        '2.6': (f'求极限 $lim_(x->{a}) (x^2-{a*a})/(x-{a})$。',
                f'Evaluate $lim_(x->{a}) (x^2-{a*a})/(x-{a})$.',
                '将分子因式分解并在 $x$ 不等于极限点时约分，得到 $x+a$。', 'Factor the numerator and cancel away from the limit point to obtain x+a.', 2*A),
        '2.7': (f'当 $x$ 不等于 ${a}$ 时，$f(x)=(x^2-{a*a})/(x-{a})$；在 $x={a}$ 时 $f(x)=k$。连续性要求 $k$ 等于多少？',
                f'For x not equal to {a}, $f(x)=(x^2-{a*a})/(x-{a})$; set f({a})=k. What k makes f continuous?',
                '可去间断点的函数值应等于该点的极限，约分后为 $x+a$。', 'At a removable discontinuity the value must equal the limit; cancellation gives x+a.', 2*A),
        '3.1': (f'用 $f(x)={a}x^2$ 在 $x=1$ 处的线性近似估计 $f(1.1)$。',
                f'Use the linear approximation of $f(x)={a}x^2$ at x=1 to estimate f(1.1).',
                '线性近似为 $L(x)=f(1)+f\'(1)(x-1)$。', 'The linear approximation is L(x)=f(1)+f\'(1)(x-1).', A+2*A*sp.Rational(1,10)),
        '3.2': (f'在整个实数轴上，$f(x)=-x^2+{2*a}x+{b}$ 的最大值是多少？',
                f'Find the maximum value on the real line of $f(x)=-x^2+{2*a}x+{b}$.',
                '令一阶导数为 0 得到 $x=a$；二阶导数为负，因此这是最大值点。', 'Set the first derivative to zero to get x=a; the negative second derivative proves a maximum.', A**2+B),
        '3.3': (f'位置为 $s(t)={a}t^3+{b}t^2$，求 $t=2$ 时的加速度。',
                f'Position is $s(t)={a}t^3+{b}t^2$. Find the acceleration at t=2.',
                '加速度是位置的二阶导数 $s\'\'(t)=6at+2b$。', 'Acceleration is the second derivative of position: s\'\'(t)=6at+2b.', 12*A+2*B),
        '3.4': (f'曲线 $y=x^3-{3*a*a}x$ 在正的临界点处有极小值。该临界点的横坐标是多少？',
                f'The graph $y=x^3-{3*a*a}x$ has a local minimum at its positive critical point. Find that x-coordinate.',
                '解 $y\'=3x^2-3a^2=0$；正根处 $y\'\'=6x>0$。', 'Solve y\'=3x²-3a²=0; at the positive root y\'\'=6x>0.', A),
        '3.5': (f'椭圆 $x^2/{a*a+b*b}+y^2/{b*b}=1$ 的两个焦点之间的距离是多少？',
                f'Find the distance between the foci of $x^2/{a*a+b*b}+y^2/{b*b}=1$.',
                '焦距的一半满足 $c^2=A^2-B^2$，两焦点间距为 $2c$。', 'The half-distance satisfies c²=A²-B²; the full distance is 2c.', 2*A),
        '3.6': (f'迭代 $x_(n+1)=(x_n+{a})/2$，从 $x_0={b}$ 开始。求 $x_2$。',
                f'Iterate $x_(n+1)=(x_n+{a})/2$ starting at $x_0={b}$. Find x_2.',
                '先将初值代入得到 $x_1$，再将 $x_1$ 代入同一函数得到 $x_2$。', 'Substitute the initial value to get x_1, then substitute x_1 to get x_2.', (B+3*A)/4),
        '3.7': (f'用牛顿法求 $x^2-{a*a+2*a}=0$，初值 $x_0={a}$。求第一次迭代值 $x_1$。',
                f'Use Newton\'s method for $x^2-{a*a+2*a}=0$ with $x_0={a}$. Find x_1.',
                '牛顿更新为 $x_1=x_0-f(x_0)/f\'(x_0)$，其中 $f\'(x)=2x$。', 'Newton\'s update is x_1=x_0-f(x_0)/f\'(x_0), with f\'(x)=2x.', A+1),
        '3.8': (f'对 $f(x)=x^2$ 在区间 $[{a},{a+2}]$ 使用中值定理。满足定理的 $c$ 是多少？',
                f'Apply the mean value theorem to $f(x)=x^2$ on [{a},{a+2}]. Find the corresponding c.',
                '令 $f\'(c)$ 等于端点割线斜率，解方程 $2c=2a+2$。', 'Set f\'(c) equal to the secant slope and solve 2c=2a+2.', A+1),
        '4.1': (f'求 $f(x)=({a}x+1)^3$ 的 $f\'(0)$。',
                f'Find f\'(0) for $f(x)=({a}x+1)^3$.',
                '链式法则给出 $f\'(x)=3a(ax+1)^2$。', 'The chain rule gives f\'(x)=3a(ax+1)².', 3*A),
        '4.2': (f'半径为 ${a}$ 的圆正在扩大，半径变化率为 ${b}$。求此刻面积变化率除以 $pi$ 的值。',
                f'A circle has radius {a}, increasing at rate {b}. Find its area growth rate divided by pi.',
                '对 $A=pi*r^2$ 关于时间求导，得到 $dA/dt=2*pi*r*dr/dt$。', 'Differentiate A=pi r² with respect to time: dA/dt=2 pi r dr/dt.', 2*A*B),
        '4.3': (f'$f(x)={a}x+{b}$ 的反函数为 $g$。求 $g\'({a+b})$。',
                f'Let g be the inverse of $f(x)={a}x+{b}$. Find g\'({a+b}).',
                '反函数求导公式是 $g\'(y)=1/f\'(g(y))$。', 'Use the inverse derivative formula g\'(y)=1/f\'(g(y)).', 1/A),
        '4.4': (f'求 $f(x)=arctan({a}x)$ 的 $f\'(0)$。',
                f'Find f\'(0) for $f(x)=arctan({a}x)$.',
                '链式法则与反正切导数给出 $f\'(x)=a/(1+a^2*x^2)$。', 'The chain rule and arctangent derivative give f\'(x)=a/(1+a²x²).', A),
        '5.1': (f'速度 $v(t)={a}+{b}t$。用曲线下面积求 $t=0$ 到 $t=2$ 的位移。',
                f'With velocity $v(t)={a}+{b}t$, find displacement from t=0 to t=2 as area under the curve.',
                '将位移写为速度的定积分，或分成矩形与三角形面积。', 'Write displacement as the definite integral of velocity, or sum the rectangle and triangle areas.', 2*A+2*B),
        '5.2': (f'已知 $F\'(x)={2*a}x$ 且 $F(0)={b}$。求 $F(2)$。',
                f'Given $F\'(x)={2*a}x$ and F(0)={b}, find F(2).',
                '积分后为 $F(x)=ax^2+C$，用初值确定 $C$。', 'Integrate to obtain F(x)=ax²+C and use the initial value for C.', 4*A+B),
        '5.3': (f'对 $f(x)={a}x$，将 $[0,1]$ 等分为 4 份。求右端点矩形面积之和。',
                f'For $f(x)={a}x$, partition [0,1] into four equal pieces. Find the right-endpoint Riemann sum.',
                '右端点为 $1/4,2/4,3/4,1$，每个矩形宽 $1/4$。', 'The right endpoints are 1/4, 2/4, 3/4, 1; every rectangle has width 1/4.', A*sp.Rational(5,8)),
        '5.4': (f'用换元法求 $integral_0^1 {2*a}x*({a}x^2+{b})^2 dx$。',
                f'Use substitution to evaluate $integral_0^1 {2*a}x*({a}x^2+{b})^2 dx$.',
                '取 $u=ax^2+b$，则 $du=2ax dx$，积分限为 $b$ 与 $a+b$。', 'Set u=ax²+b, so du=2ax dx and the bounds become b and a+b.', ((A+B)**3-B**3)/3),
        '5.5': (f'求定积分 $integral_1^3 ({a}x+{b}) dx$。',
                f'Evaluate $integral_1^3 ({a}x+{b}) dx$.',
                '先求原函数 $ax^2/2+bx$，再计算上限值减下限值。', 'Use the antiderivative ax²/2+bx, evaluated at the upper bound minus the lower bound.', 4*A+2*B),
        '5.6': (f'求 $f(x)={a}x^2+{b}$ 在 $[0,3]$ 上的平均值。',
                f'Find the average value of $f(x)={a}x^2+{b}$ on [0,3].',
                '函数平均值等于区间上的积分除以区间长度。', 'The average value is the integral over the interval divided by its length.', 3*A+B),
        '5.7': (f'$F(x)=integral_0^(x^2) ({a}t+{b}) dt$。求 $F\'(1)$。',
                f'Let $F(x)=integral_0^(x^2) ({a}t+{b}) dt$. Find F\'(1).',
                '微积分基本定理结合链式法则给出 $F\'(x)=(ax^2+b)*2x$。', 'The fundamental theorem and chain rule give F\'(x)=(ax²+b)*2x.', 2*(A+B)),
        '5.8': (f'用两个等宽子区间的梯形法估计 $integral_0^2 {a}x^2 dx$。',
                f'Use the composite trapezoidal rule with two equal subintervals to estimate $integral_0^2 {a}x^2 dx$.',
                '步长为 1，梯形公式为 $(f(0)+2f(1)+f(2))/2$。', 'The step width is 1; the trapezoidal formula is (f(0)+2f(1)+f(2))/2.', 3*A),
        '6.1': (f'指数函数 $f(x)={b}*{a}^x$。求 $f(3)/f(1)$。',
                f'For the exponential function $f(x)={b}*{a}^x$, find f(3)/f(1).',
                '约去共同系数，再用同底数幂相除时指数相减的法则。', 'Cancel the common coefficient and subtract exponents when dividing powers of the same base.', A**2),
        '6.2': (f'求 $f(x)={a}*e^({b}x)$ 的 $f\'(0)$。',
                f'Find f\'(0) for $f(x)={a}*e^({b}x)$.',
                '指数函数求导并乘以内函数导数，得到 $f\'(x)=ab e^(bx)$。', 'Differentiate the exponential and multiply by the inner derivative: f\'(x)=ab e^(bx).', A*B),
        '6.3': (f'某物质初始量为 ${a}$，每经过一个半衰期减半。经过 3 个半衰期剩余多少？',
                f'A substance starts with amount {a} and halves each half-life. How much remains after three half-lives?',
                '每个半衰期乘以 $1/2$，连续三个半衰期共乘以 $(1/2)^3$。', 'Multiply by 1/2 for each half-life, giving a factor of (1/2)³.', A/8),
        '6.4': (f'求 $f(x)=ln({a}x^2)$ 在 $x={b}$ 处的导数（$x>0$）。',
                f'Find f\'({b}) for $f(x)=ln({a}x^2)$, with x>0.',
                '用对数导数 $u\'/u$，约分得到 $f\'(x)=2/x$。', 'Use the logarithmic derivative u\'/u and simplify to f\'(x)=2/x.', 2/B),
        '6.5': (f'可分离方程 $dy/dt={a}y$ 满足 $y(0)={b}$。求 $y(ln(2)/{a})$。',
                f'The separable equation $dy/dt={a}y$ has y(0)={b}. Find y(ln(2)/{a}).',
                '分离变量并积分，再用初值得到 $y(t)=b e^(at)$。', 'Separate variables, integrate, and use the initial value to get y(t)=b e^(at).', 2*B),
        '6.6': (f'在 $x>0$ 上，$dy/dx={b}y/x$ 且 $y(1)={a}$。求 $y(2)$。',
                f'For x>0, $dy/dx={b}y/x$ and y(1)={a}. Find y(2).',
                '分离变量积分得 $ln(y)=b ln(x)+C$，初值给出 $y=a x^b$。', 'Separate and integrate to get ln(y)=b ln(x)+C; the initial value gives y=a x^b.', A*2**B),
        '6.7': (f'已知 $cosh(t)={a}$ 且 $t>0$。求 $sinh(t)^2$。',
                f'Given cosh(t)={a} and t>0, find sinh(t)².',
                '使用恒等式 $cosh(t)^2-sinh(t)^2=1$。', 'Use the identity cosh(t)²-sinh(t)²=1.', A**2-1),
        '7.1': (f'用分部积分求 $integral_0^1 {a}x*e^x dx$。',
                f'Use integration by parts to evaluate $integral_0^1 {a}x*e^x dx$.',
                '取 $u=x,dv=e^x dx$，得到原函数 $a(x-1)e^x$。', 'Take u=x and dv=e^x dx to obtain the antiderivative a(x-1)e^x.', A),
        '7.2': (f'求 $integral_0^(pi/2) {a}sin(x)cos(x) dx$。',
                f'Evaluate $integral_0^(pi/2) {a}sin(x)cos(x) dx$.',
                '取 $u=sin(x)$，积分化为 $a integral_0^1 u du$。', 'Set u=sin(x), reducing the integral to a times the integral of u from 0 to 1.', A/2),
        '7.3': (f'求 $integral_0^({a}/2) 1/sqrt({a*a}-x^2) dx$，将结果除以 $pi$ 后是多少？',
                f'Evaluate $integral_0^({a}/2) 1/sqrt({a*a}-x^2) dx$ and divide the result by pi.',
                '取 $x=a sin(theta)$，积分化为从 0 到 $pi/6$ 的 $dtheta$。', 'Set x=a sin(theta); the integral becomes the integral of dtheta from 0 to pi/6.', sp.Rational(1,6)),
        '7.4': (f'将 $({a+b}x+{a})/(x(x+1))$ 写成 $A/x+B/(x+1)$。求 $A$。',
                f'Decompose $({a+b}x+{a})/(x(x+1))$ as A/x+B/(x+1). Find A.',
                '通分后分子为 $(A+B)x+A$，比较常数项。', 'Combining fractions gives numerator (A+B)x+A; compare constant coefficients.', A),
        '7.5': (f'求反常积分 $integral_1^infinity {a}/x^2 dx$。',
                f'Evaluate the improper integral $integral_1^infinity {a}/x^2 dx$.',
                '先积分到有限上界 $M$，得到 $a-a/M$，再令 $M$ 趋于无穷。', 'Integrate to a finite upper bound M to get a-a/M, then let M tend to infinity.', A),
        '8.1': (f'曲线 $y={a}x$ 与 $y=0$ 在 $[0,1]$ 围成的区域绕 $x$ 轴旋转。体积除以 $pi$ 是多少？',
                f'Revolve the region under $y={a}x$ on [0,1] about the x-axis. Find the volume divided by pi.',
                '圆盘截面积为 $pi*(ax)^2$，对 $x$ 积分后再除以 $pi$。', 'Disk cross-sections have area pi*(ax)²; integrate and divide by pi.', A**2/3),
        '8.2': (f'求直线 $y=({a}/3)x$ 在 $0<=x<=3$ 上的弧长的平方。',
                f'Find the square of the arc length of $y=({a}/3)x$ for 0<=x<=3.',
                '弧长为 $integral_0^3 sqrt(1+(a/3)^2) dx$，再平方。', 'Arc length is the integral of sqrt(1+(a/3)²) from 0 to 3; then square it.', A**2+9),
        '8.3': (f'水平线段 $y={a}, 0<=x<={b}$ 绕 $x$ 轴旋转形成曲面（不含端盖）。曲面积除以 $pi$ 是多少？',
                f'Revolve $y={a}, 0<=x<={b}$ about the x-axis (no end caps). Find the surface area divided by pi.',
                '旋转曲面积为 $2*pi integral y*sqrt(1+(y\')^2) dx$，此处 $y\'=0$。', 'Use surface area=2 pi times the integral of y sqrt(1+(y\')²); here y\'=0.', 2*A*B),
        '8.4': (f'概率密度为 $p(x)=c*x$，定义在 $0<=x<={a}$，区间外为 0。归一化常数 $c$ 是多少？',
                f'A probability density is p(x)=c*x for 0<=x<={a}, and zero elsewhere. Find c.',
                '概率密度的积分为 1，因此 $c*a^2/2=1$。', 'The integral of a density is 1, so c*a²/2=1.', 2/A**2),
        '8.5': (f'细杆位于 $0<=x<={a}$，线密度为 $rho(x)={b}x$。求质心的横坐标。',
                f'A rod on 0<=x<={a} has linear density rho(x)={b}x. Find its center-of-mass coordinate.',
                '质心是一次矩除以质量，即 $integral x*rho dx / integral rho dx$。', 'The center of mass is the first moment divided by mass: integral(x*rho)/integral(rho).', 2*A/3),
        '8.6': (f'弹簧遵循 $F(x)={a}x$。将其从自然长度拉伸到 $x={b}$ 所做的功是多少？',
                f'A spring obeys F(x)={a}x. Find the work to stretch it from its natural length to x={b}.',
                '变力做功为 $integral_0^b F(x) dx$。', 'Work by a variable force is the integral of F(x) from 0 to b.', A*B**2/2),
    }
    if label not in cases:
        raise ValueError(f"No authored challenge template for section {label}")
    return item(*cases[label])


def _math(value):
    return sp.sstr(value).replace('**', '^')


def working(label, a, b):
    """Concrete substitution steps, kept unsimplified for the ordering tasks."""
    return {
        '1.1': f'(({a}*3^2+{b}*3)-({a}+{b}))/(3-1)',
        '1.2': f'2*{a}*{b}', '1.3': f'3*{a}*2^2+{b}',
        '1.4': f'sqrt({a}^2*{b}^2)', '1.5': f'{a}*2*(3/5)*(4/5)', '1.6': f'{a}*sin(pi/2)',
        '2.1': f'2*{a}*3', '2.2': f'3*{a}*2^2+2*{b}*2',
        '2.3': f'({a}+{b})-2*{a}', '2.4': f'{a}*cos(0)-{b}*sin(0)',
        '2.5': f'({a}-{b})/(1+1)^2', '2.6': f'{a}+{a}', '2.7': f'{a}+{a}',
        '3.1': f'{a}+2*{a}*(11/10-1)', '3.2': f'-{a}^2+{2*a}*{a}+{b}',
        '3.3': f'6*{a}*2+2*{b}', '3.4': f'sqrt({3*a*a}/3)',
        '3.5': f'2*sqrt({a*a+b*b}-{b*b})', '3.6': f'(({b}+{a})/2+{a})/2',
        '3.7': f'{a}-({a}^2-{a*a+2*a})/(2*{a})',
        '3.8': f'(({a+2}^2-{a}^2)/2)/2',
        '4.1': f'3*{a}*({a}*0+1)^2', '4.2': f'2*{a}*{b}',
        '4.3': f'1/{a}', '4.4': f'{a}/(1+{a}^2*0^2)',
        '5.1': f'{a}*2+{b}*2^2/2', '5.2': f'{a}*2^2+{b}',
        '5.3': f'{a}*(1/4+2/4+3/4+1)/4', '5.4': f'(({a}+{b})^3-{b}^3)/3',
        '5.5': f'({a}*3^2/2+{b}*3)-({a}/2+{b})',
        '5.6': f'({a}*3^3/3+{b}*3)/3', '5.7': f'({a}*1^2+{b})*2*1',
        '5.8': f'({a}*0^2+2*{a}*1^2+{a}*2^2)/2',
        '6.1': f'({b}*{a}^3)/({b}*{a}^1)', '6.2': f'{a}*{b}*exp(0)',
        '6.3': f'{a}*(1/2)^3', '6.4': f'2/{b}', '6.5': f'{b}*exp(log(2))',
        '6.6': f'{a}*2^{b}', '6.7': f'{a}^2-1',
        '7.1': f'{a}*((1-1)*exp(1)-(0-1)*exp(0))', '7.2': f'{a}*(1^2-0^2)/2',
        '7.3': '(pi/6-0)/pi', '7.4': f'({a+b}*0+{a})/(0+1)', '7.5': f'{a}*(1-0)',
        '8.1': f'{a}^2*(1^3-0^3)/3', '8.2': f'3^2*(1+({a}/3)^2)',
        '8.3': f'2*{a}*sqrt(1+0^2)*{b}', '8.4': f'1/({a}^2/2)',
        '8.5': f'({b}*{a}^3/3)/({b}*{a}^2/2)', '8.6': f'{a}*({b}^2-0^2)/2',
    }[label]


def question(section, qtype, language, excluded):
    """At most 50 exclusions arrive via the API; vary actual problem parameters.

    Enumerating more parameter sets than exclusions ensures progress without
    silently repeating a stem or changing the section/format/difficulty.
    """
    normalize = lambda value: value.strip().lower().replace(' ', '').replace('$', '')
    blocked = {normalize(stem) for stem in excluded or []}
    start = random.randrange(2, 12)
    for offset in range(len(blocked) + 1):
        a, b = start + offset, random.randrange(2, 10)
        stem, rule, expression, answer = exercise(section['label'], a, b, language)
        zh = language == 'zh'
        result = _math(answer)
        calculation = working(section['label'], a, b)
        steps = [rule,
                 (f'将已知量代入，所求数值可写为 ${calculation}$。' if zh else f'Substituting the given values yields ${calculation}$.'),
                 (f'计算并化简，所求值为 ${result}$。' if zh else f'Evaluate and simplify: the requested value is ${result}$.')]
        data = dict(stem=stem, explanation=rule + ' ' + steps[-1], key_idea=section['display_title'],
                    solution_steps=steps, final_answer=result)
        if qtype == 'single_choice':
            values = [answer, answer+1, answer-1, answer+2]
            random.shuffle(values)
            data.update(options=[f'${_math(value)}$' for value in values], correct_index=values.index(answer))
        elif qtype == 'multiple_choice':
            data['stem'] += (' 令 $R$ 表示所求数值，选择所有正确的比较关系。' if zh else ' Let R be the requested value. Select every true comparison.')
            choices = [(f'$R > {_math(answer-1)}$', True), (f'$R < {_math(answer+1)}$', True),
                       (f'$R > {_math(answer+2)}$', False), (f'$R < {_math(answer-2)}$', False)]
            random.shuffle(choices)
            data.update(options=[x[0] for x in choices], correct_indices=[i for i, x in enumerate(choices) if x[1]])
        elif qtype == 'fill_blank':
            data['stem'] += (' 所求数值为 ___（分数可写成 p/q）。' if zh else ' The requested value is ___ (fractions may be written as p/q).')
            alternatives = [result]
            if answer.is_Rational and (10**12 % int(answer.q)) == 0:
                alternatives.append(str(float(answer)))
            data['blanks'] = [{'answer': result, 'alternatives': alternatives}]
        elif qtype == 'drag_order':
            data['stem'] += (' 将下列解题步骤按推导顺序排列。' if zh else ' Arrange the solution steps in derivation order.')
            data['steps'] = steps
        else:
            raise ValueError(f'Unsupported challenge format: {qtype}')
        if normalize(data['stem']) not in blocked:
            return data
    raise ValueError('Challenge template could not produce a distinct question')
