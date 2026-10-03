作者询问信草稿（未发送）

收件人可使用论文首页公开的第一作者邮箱 `yutingz@cse.unsw.edu.au`。作者和联系地址来自本地与官方 SHA256 一致的论文，不使用同名 GitHub 账户推断身份。

Subject: Request for GT-PSC implementation and k-star mechanism details (ACL 2026)

Dear Yuting Zhang and coauthors,

I am working on reproducing your paper, “Agent-based Substructure Counting under Local Differential Privacy” (ACL 2026, 2026.acl-long.1032). I found the paper and Responsible NLP Checklist on ACL Anthology, but could not locate the implementation. Would you be willing to share the repository or the Python scripts for GT-PSC and GT-PSC-B, particularly the 2-star and 3-star experiments in Tables 2 and 3?

Our implementation follows the public description: for epsilon=2 and k-star counting, epsilon1=0, epsilon2=0.4, and epsilon3=1.6. We estimate the maximum from independently Laplace-perturbed degrees, clip local degrees to the resulting threshold D, compute C(min(d_i,D),k), add independent Laplace noise of scale C(D,k-1)/epsilon3 at every node, and sum the reports before clamping the final result to zero.

Across six datasets, our GT-Naive values are close to Table 2. However, the 2-star GT-PSC errors remain higher. For example, on Les Miserables we obtain approximately 0.083, compared with 0.0444 in Table 2. Our graph has 77 nodes, 254 edges, maximum degree 36, and 2-star count 2808. We have also compared the rounding behavior in Imola et al.'s 2021 public implementation, but this does not explain the difference.

It would be very helpful to clarify:

1. The exact k-star sensitivity formula and whether it uses a shared maximum degree, each node's degree, or another bound.
2. How the noisy maximum is rounded for projection and for sensitivity; whether the true local neighbor lists are clipped.
3. The actual epsilon allocation and Laplace scale used for k-star reporting when the noisy-graph stage is omitted.
4. Whether every node reports independent noise and whether any correction, filtering, averaging, or clipping is applied before or after aggregation.
5. Whether you could share the preprocessed graphs or their degree sequences, the complete k-star DP/algorithm library entries, and the per-run GT results or seeds for Tables 2 and 3.

Our current checks identify a mismatch with this particular interpretation of the mechanism, not a conclusion about your implementation. We would appreciate any guidance on the intended implementation details.

Thank you for your time and for the paper.

Best regards,
[Your name]
