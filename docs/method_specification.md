# Method specification

This project uses triangular fuzzy TOPSIS with Chen's (2000) vertex distance, criterion-distance summation, and closeness coefficient. It explicitly adapts the original group linguistic-rating setting to measured field ranges and crisp equal weights. These modelling choices must be cited as project choices, not as unchanged formulas from Chen.

For alternative i and priority-oriented criterion j, the field triangle is x_ij=(l_ij,c_ij,u_ij), with l <= c <= u. For count data these are minimum, median and maximum hourly rates from the repeated observation windows. For audit data they are documented lower, central and upper assessor ratings. The triangular membership shape is an approximation supported by the observed bounds, not a probability distribution or a calibrated uncertainty interval.

Normalize criterion j with L_j=min_i l_ij and U_j=max_i u_ij. For q in {l,c,u}, z_ijq=(x_ijq-L_j)/(U_j-L_j) when U_j>L_j. If U_j=L_j, the criterion is constant and excluded. Other criteria identical across alternatives are also excluded; the remaining weights are renormalized. All five project criteria increase priority, so no cost reversal is applied to them. A separate crisp benefit/cost helper is included for transparent baselines or future documented criteria.

For active criteria, provisional weights are equal, w_j=1/m. Form v_ij=(w_j z_ijl, w_j z_ijc, w_j z_iju). The project-specific attainable ideals are A_j+=(w_j,w_j,w_j) and A_j-=(0,0,0). The vertex metric is d(a,b)=sqrt([(a_l-b_l)^2+(a_c-b_c)^2+(a_u-b_u)^2]/3). Total distances **sum over criteria**: D_i+=sum_j d(v_ij,A_j+), D_i-=sum_j d(v_ij,A_j-). Closeness C_i=D_i-/(D_i++D_i-), sorted descending. Exact ties are ordered by alternative ID for stable output.

The score depends on the included alternatives because min/max bounds do. It is not a probability. A zero denominator or non-discriminating matrix is an error, not a result. Check data plausibility, scale assumptions, and potential double counting before using any ranking.

The simple-priority baseline uses central observations only. For each nonconstant benefit criterion its crisp value is (x_ij−min_i x_ij)/(max_i x_ij−min_i x_ij), then the active normalized values are averaged with equal weights. A constant central criterion is omitted. Spearman correlation uses average ranks for ties and is left undefined when an entire ranking has a single tied value. Display order for exact score ties is alternative ID.
