PSC 作者实现检索与 k-star 深入研究（2026-09-28）

截至 2026-09-28，本次未找到能够确认归属于《Agent-based Substructure Counting under Local Differential Privacy》作者的公开实现。已找到其引用的 Imola、Murakami、Chaudhuri（USENIX Security 2021）官方代码，并完成源码级比较和独立数值验证。不能由“未找到”推出“作者一定没有公开”；部分作者主页无法访问，未进行需登录的 GitHub 全代码搜索。

研究得到一个比上一轮更强的结论：在当前 ML、EE、PM 数据上，仅调整统一度阈值、取整和隐私预算，无法让当前机制族的理论期望达到论文 2-star 的点值。这里的机制族有明确边界：本地度裁剪、共同灵敏度、所有节点独立 Laplace 报告、直接求和、最终非负截断。结论不覆盖其他估计器，也不意味着有限次实验的平均值绝不可能低于理论期望。

本次只新增研究文档、来源快照和离线脚本，没有修改生产算法或调用付费模型，也没有给作者发送消息。

**1. 实际检索了什么**

| 来源 | 核验结果 | 限制 |
|---|---|---|
| ACL 官方论文页 | 标识符 2026.acl-long.1032，题名与五位作者一致；未发现代码链接 | 页面上的 ACL Anthology GitHub 链接是文献网站自身的仓库 |
| 官方 PDF | 在线重新下载，SHA256 与本地 PDF 完全一致；检查全部嵌入 URI，未发现仓库链接 | 不能排除未链接的外部仓库 |
| ACL 附件 | 有 Responsible NLP Checklist，没有发现代码包或额外算法附件；Checklist 没有代码地址 | Checklist 也没有明确承诺公开代码 |
| ACL 第一作者页 | 提供 ORCID 0009-0002-3988-730X | 该链接提供可靠作者身份锚点，避免同名误认 |
| ORCID 公开资料 | researcher-urls 为空；既往论文包括 ICDE 2025 LDP truss、EDBT 2024 bipartite community search 等 | 未发现代码主页；公开信息可能不完整 |
| GitHub repository/README 搜索 | 完整题名及短题名命中的是 SecAI_Radar 文献列表，非作者实现；GT-PSC、DOI 的 README 搜索无结果 | 仓库搜索不等于全代码搜索，且有索引覆盖限制 |
| GitHub issues 搜索 | 精确短题名无结果 | 未以此认定不存在其他名称的讨论 |
| arXiv API | 精确短题名查询无结果 | 不能排除其他题名的预印本 |
| 作者主页 | UNSW 第一作者地址返回 403，另一作者主页超时 | 无法核验，不作为“无代码”的证据 |
| 常规搜索 | web 搜索未返回可引用结果；Google 要求 JS、DuckDuckGo 人机验证，Bing 返回不相关内容 | 这些失败不作为不存在代码的证据 |

可直接核验的来源：

- PSC 官方页面：https://aclanthology.org/2026.acl-long.1032/
- PSC 官方 PDF：https://aclanthology.org/2026.acl-long.1032.pdf
- Checklist：https://aclanthology.org/attachments/2026.acl-long.1032.checklist.pdf
- 第一作者 ACL 页面：https://aclanthology.org/people/yuting-zhang/
- ORCID：https://orcid.org/0009-0002-3988-730X
- 引用论文：https://www.usenix.org/conference/usenixsecurity21/presentation/imola
- 引用论文官方代码：https://github.com/LDPGraphStatistics/LDPGraphStatistics
- 本次核验源码的固定版本：https://github.com/LDPGraphStatistics/LDPGraphStatistics/blob/a0707f6fc26b855c0ed5e8f052cc4117768948ed/cpp/EvalLossLocal.cpp

公开下载、搜索返回和文件哈希保存在 `results/research/2026-09-28-author-implementation/`。源码按 MIT 许可保留 LICENSE。该源码属于 2021 年基础算法，不能称为 PSC 作者实现。

**2. 引用论文源码究竟与本项目差在哪里**

USENIX 2021 的 Section 4.1 / Algorithm 1 使用本地邻居度裁剪、组合数计数和独立 Laplace 报告。源码对应 `CalcNSMaxDeg`、`CalcNLocSt`。

| 环节 | 当前 PSC 项目 | Imola 2021 C++ 源码 |
|---|---|---|
| 带噪最大度 M | max_i(d_i+Lap(1/epsilon2)) | 同样的最大值估计，另外限制在 [0,n-1] |
| 本地投影阈值 | ceil(M) | floor(M) |
| 2-star 灵敏度 | ceil(M) | 未取整的连续 M |
| 3-star 灵敏度 | C(ceil(M),2) | M(M-1)/2 |
| epsilon=2 的预算 | epsilon2=.4，报告 1.6 | 默认最大度 .2，报告 1.8 |
| 报告节点数 | 全体 n 个节点 | 全体 n 个节点 |
| 星计数的最终非负截断 | 有 | `CalcNLocSt` 和 loss 评估路径没有；clustering coefficient 函数只改自己的值参数 |

注意基础论文的文字说明把 floor(M) 作为下一轮输入，C++ 却对 GS 保留连续 M。论文正文与源码不能混为同一个精确变体。源码也使用 n-1 作为无优化最大度，而 PSC 正文与当前项目使用 n 的组合数上界。

为排除翻译错误，本次从下载源码中提取上述两个函数的原始函数体，保留原逻辑，仅用固定噪声序列替换随机采样器。在六图、两种预算、共 1200 个样本上，与独立 Python 公式比较：2-star 输出最大绝对差约 2.62e-10，3-star 约 8.85e-9，采样调用数一致。此验证不声称 NumPy 与 StatsLib 的随机数流相同，也没有运行原仓库的完整可执行程序。

对每图 50000 次同基础噪声模拟，六图平均 RE 为：

| 机制 | 2-star | 3-star |
|---|---:|---:|
| 当前机制，本次独立种子 | 0.11418 | 0.45134 |
| C++ 的 floor 投影 + 连续 GS，保留 PSC 预算和最终截断 | 0.11162 | 0.43252 |
| 基础论文的 floor 投影 + 整数 GS，保留 PSC 预算和最终截断 | 0.10870 | 0.41305 |
| C++ 默认预算 .2/1.8、原报告与 loss 语义 | 0.14476 | 1.03660 |
| 上一项加上 PSC 的最终非负截断 | 0.14426 | 0.75547 |
| PSC 论文 Table 2 | 0.0647 | 0.3649 |

这些变体并没有解释 2-star 差距。基础代码默认分给最大度的预算更少，使 CU/CS 的最大度噪声更大；因此照搬默认设置反而恶化结果。此处数值比上一轮略有变化来自预先固定的新种子，不能解释成生产代码改进。

**3. 更强的检查：当前机制族究竟能做到多好**

只观察原来的 noisy max 并不够，因为仍可能怀疑“换一个更好的阈值或预算就能对齐”。本次直接给予当前机制族有利条件：

1. 允许免费知道当前图，枚举 D=0,...,n-1，选择使期望 RE 最小的整数阈值。
2. 省去最大度估计的隐私开销，把完整 epsilon=2 用于计数报告。
3. 使用固定 D 下更紧的 GS=C(D-1,k-1)，并允许最终非负截断。

这只是理想化比较，免费依赖真实图选择 D 不是可直接发布的隐私算法。目的在于给这一机制族一个过于有利的数值参照。

2-star 的结果：

| 数据集 | 最佳整数 D | 该机制族的最优期望 RE | 论文 GT-PSC |
|---|---:|---:|---:|
| CU | 7 | 0.06233 | 0.1062 |
| Do | 11 | 0.04898 | 0.0585 |
| ML | 35 | **0.06067** | **0.0444** |
| CS | 11 | 0.11443 | 0.1210 |
| EE | 40 | **0.03646** | **0.0295** |
| PM | 236 | **0.03571** | **0.0284** |

ML、EE、PM 的论文点值低于这个理想化机制族的最小期望。若论文均值在重复实验中稳定复现，则至少有一项假设不同：实际输入图、敏感度／报告机制、报告独立性或同尺度假设、聚合／校正估计器、评估实现。它不支持继续把问题只归咎于 ceil 或 epsilon2 的比例。

这一结论不是所有 LDP 算法的下界，也不是对论文错误的证明。论文报告的是 1000 次有限样本均值，没有逐次结果和方差；有限样本均值可以低于期望。对真实作者机制也尚未取得直接证据。

为什么随机 D 不能解决这个机制族内的问题：给定 D 后风险为 R(D)，若报告噪声独立于用于选择 D 的随机量，则 E_D[R(D)] 不小于 min_D R(D)。若另有使用带噪度报告的估计器或数据校正，该假设便不再覆盖它。

**4. 期望误差的推导和验证**

定义当前图的真值 T、裁剪后的无噪声总计数 A(D)、报告尺度 b：

    T = sum_i C(d_i,k)
    A(D) = sum_i C(min(d_i,D),k), 0 <= A <= T
    S = sum_i L_i, L_i iid Laplace(0,1)
    Y = max(0,A+bS)
    H_n(t) = E[(S-t)_+], t >= 0

利用 S 的对称性、B=T-A，可以直接得到：

    E|Y-T| = B + 2b H_n(B/b) - b H_n(A/b)

b=0 时使用 |A-T|。最后一项正好表示最终非负截断减少的绝对误差。

S 也可写成两个独立 Gamma(n,1) 变量之差。对 s>=0，其密度有有限多项式表达：

    f_S(s) = (1/2) sum_{j=0}^{n-1} w_j * exp(-s)*s^j/j!
    w_j = (2n-2-j)! / [(n-1-j)! (n-1)! 2^(2n-2-j)]
    sum_j w_j = 1

由此积分得到 H_n，脚本以对数概率计算，避免阶乘溢出。这是针对当前风险函数的独立数学推导，不是引用论文声称的结果。

验证包括：n=1 与单 Laplace 的闭式一致；H_n(0)=Gamma(n+1/2)/(sqrt(pi)Gamma(n))；n∈{1,2,49,77,143,453} 下，四组不同 A/T/b，各 300000 个 Gamma 差样本与闭式比较，全部通过六倍标准误检查，最大偏差为 2.37 个标准误。检查覆盖 b=0、A=0、A=T 和 0<A<T。

为什么给足报告 epsilon=2 是上述低误差最优值的有利边界，需要考虑非负截断，不能一概假设加噪越大风险越大。对于 A>=T/2，B<=A，风险对 b 的导数可写为 2J(B/b)-J(A/b)>=0，其中 J(t)=E[S 1(S>t)] 随 t 减少。对于 A<T/2，至少一半噪声满足 S<=0，故期望 RE >= (T-A)/(2T) > 1/4。本表的所有最优 2-star RE 都小于 1/4，所以更小的报告 epsilon 无法产生更优的遗漏解。这是本次枚举推广到全部 epsilon3<=2 的依据。

**5. 一个可继续推进的新方法：先发布度数，再校正组合数**

找不到作者实现不必阻止独立方法研究。对于只依赖度数的 k-star，可以让每个节点仅发布：

    y_i = d_i + Laplace(0,b), b=1/epsilon

在 PSC 使用的每节点单比特 epsilon-edge LDP 定义下，度数敏感度为 1。之后的星计数只使用 y_i，属于后处理；2-star 和 3-star 可以复用同一次发布。这里不宣称完整图转录也满足相同 epsilon 的 relationship DP，后者与论文定义须分别讨论。

不能直接把 C(y_i,k) 当无偏估计，因为非线性变换会引入噪声矩偏差。由 E[L]=0、E[L²]=2b²、E[L³]=0，得到：

    2-star: sum_i [y_i(y_i-1)/2 - b²]
    3-star: sum_i [y_i(y_i-1)(y_i-2)/6 - b²(y_i-1)]

两式在最终截断前都对真实总计数无偏。节点侧不能先把 y_i 或校正项截为非负；那会破坏推导。最终求和后可以选择非负截断，但需说明它使估计不再严格无偏。

这条路线完全绕开全图统一 D 放大所有节点报告噪声的问题，但没有消除高阶统计本身的风险。2-star 单节点校正估计的方差是：

    2b²(d_i-1/2)² + 5b⁴

所以方差仍随实际度数增长；最坏情况下仍可能达到与 n*D² 同级的量级，不违反基础论文对一轮 LDP 最坏情况的讨论。高阶任务和其他图分布也需要单独验证。

本次 epsilon=2、每图 100000 次独立模拟，使用最终非负截断：

| 数据集 | 新候选 2-star RE | 新候选 3-star RE |
|---|---:|---:|
| CU | 0.03951 | 0.07476 |
| Do | 0.02649 | 0.04610 |
| ML | 0.01504 | 0.02626 |
| CS | 0.03820 | 0.06897 |
| EE | 0.00929 | 0.01650 |
| PM | 0.00279 | 0.00479 |
| 六图平均 | 0.02189 | 0.03956 |

验证包括：d=0..453、两种任务，共 908 组噪声矩代数检查；每图的截断前平均估计与无偏期望一致性检查；结果 JSON 记录解析方差、经验方差和标准误。这个候选是独立研究方向，不是作者 GT-PSC 的重建，也不主张方法新颖性或已经验证真实 LLM 执行效果。它可作为下一轮基线，不能替换原表并宣称论文复现成功。

**6. 接下来如何决策**

若目标是忠实复现：保留当前实现和所有机制候选，优先向作者索取 GT-PSC、GT-PSC-B 的 k-star 脚本与完整 DP 库。邮件草稿已放在 `docs/PSC_AUTHOR_INQUIRY_DRAFT.md`，未发送。重点索取逐节点报告公式、数据的度向量、阈值取整、预算和 Table 2/3 的逐次结果。现在的问题足够具体，可以避免笼统询问“为什么复现不一致”。

若目标是降低实际统计误差：可以先将 noisy-degree moment correction 加为单独纯代码基线，核对完整威胁模型和所有输出，再接入 agent 的后处理流程。它与当前 PSC 使用不同估计器，必须单独命名并记录隐私预算，不得同时重复发布原始计数报告而仍声称总预算为 2。

当前没有证据支持“通过更换更强 LLM 就能对齐论文 GT”。已有 pilot 的 k-star 原始计数基本正确；新研究进一步表明，剩余关键问题在机制定义和可复现证据。

**7. 可复现文件**

- `results/research/2026-09-28-author-implementation/source_manifest.json`：来源、源码 commit、文件哈希。
- `upstream/EvalLossLocal.cpp` 与 `upstream/LICENSE`：引用论文的官方源码快照。
- `research_mechanism.py`、`mechanism_research.json`：来源变体、风险闭式校验、全部阈值枚举。
- `upstream_function_harness.cpp`、`verify_upstream_translation.py`、`upstream_translation_check.json`：C++ 原函数的噪声配对验证。
- `noisy_degree_candidate.py`、`noisy_degree_candidate.json`：独立改进候选及其验证。

运行命令：

```bash
.venv/bin/python results/research/2026-09-28-author-implementation/research_mechanism.py
g++ -std=c++17 -O2 results/research/2026-09-28-author-implementation/upstream_function_harness.cpp -o /tmp/psc_upstream_function_harness
.venv/bin/python results/research/2026-09-28-author-implementation/verify_upstream_translation.py
.venv/bin/python results/research/2026-09-28-author-implementation/noisy_degree_candidate.py
```

边界：官方页面、PDF、Checklist、ORCID 和仓库索引都没有提供本次可以确认的 PSC 实现；作者主页访问存在缺口，不能证明全网不存在代码。引用源码和本次推导缩小了原因范围，但仍不能替作者确认实际使用了哪种机制。
