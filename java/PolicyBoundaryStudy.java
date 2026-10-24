import java.util.*;

/** Owned, benign post-decoding policy-transfer study; not a new wire schema. */
public final class PolicyBoundaryStudy {
    private static final class Frozen {
        private final int[] tenant, quota, next, roots;
        Frozen(int[] a, int[] b, int[] c, int[] r) {
            tenant=a.clone(); quota=b.clone(); next=c.clone(); roots=r.clone();
        }
        int[] roots() { return roots.clone(); }
        int tenant(int i) { return tenant[i]; }
        int quota(int i) { return quota[i]; }
        int next(int i) { return next[i]; }
    }
    private static BitSet closure(int[] links, int[] roots, int count) {
        BitSet live=new BitSet(links.length);
        for(int j=0;j<count;j++) {
            int i=roots[j];
            while(i>=0 && !live.get(i)) { live.set(i); i=links[i]; }
        }
        return live;
    }
    private static boolean policy(int[] tenant,int[] quota,int[] links,BitSet live,int p) {
        // p=0: tenant-isolated, non-increasing delegated quota. p=1: empty or quorum.
        if(p==1) return live.isEmpty() || live.cardinality()>=2;
        for(int i=live.nextSetBit(0);i>=0;i=live.nextSetBit(i+1)) {
            int t=links[i];
            if(t>=0 && (tenant[i]!=tenant[t] || quota[t]>quota[i])) return false;
        }
        return true;
    }
    private static int[] proof(int[] a,int[] b,int[] c,int[] r,int p) {
        ArrayList<Integer> words=new ArrayList<>();
        for(int j=0;j<=r.length;j++) {
            BitSet k=closure(c,r,j);
            words.add(k.cardinality());
            for(int i=k.nextSetBit(0);i>=0;i=k.nextSetBit(i+1)) words.add(i);
            words.add(policy(a,b,c,k,p)?1:0);
        }
        return words.stream().mapToInt(Integer::intValue).toArray();
    }
    private static Frozen receive(int[] a,int[] b,int[] c,int[] r,int p,int[] evidence) {
        // These arrays represent already-decoded primitive data. Clone before inspecting.
        a=a.clone(); b=b.clone(); c=c.clone(); r=r.clone();
        int[] e=evidence==null?null:evidence.clone();
        if(a.length<1 || a.length>128 || b.length!=a.length || c.length!=a.length || r.length>128)
            throw new IllegalArgumentException("dimensions");
        for(int i=0;i<a.length;i++)
            if(a[i]<0 || a[i]>1 || b[i]<0 || b[i]>2 || c[i]<-1 || c[i]>=a.length)
                throw new IllegalArgumentException("domain");
        for(int x:r) if(x<0 || x>=a.length) throw new IllegalArgumentException("root");
        if(e==null) return policy(a,b,c,closure(c,r,r.length),p)?new Frozen(a,b,c,r):null;
        int at=0;
        for(int j=0;j<=r.length;j++) {
            BitSet k=closure(c,r,j);
            if(at>=e.length || e[at++]!=k.cardinality()) return null;
            for(int i=k.nextSetBit(0);i>=0;i=k.nextSetBit(i+1))
                if(at>=e.length || e[at++]!=i) return null;
            boolean ok=policy(a,b,c,k,p);
            if(at>=e.length || e[at++]!=(ok?1:0) || !ok) return null;
        }
        return at==e.length?new Frozen(a,b,c,r):null;
    }
    private static int[] digits(int x,int base,int n) {
        int[] out=new int[n];
        for(int i=0;i<n;i++) { out[i]=x%base; x/=base; }
        return out;
    }
    public static void main(String[] args) {
        System.out.println("policy,cases,final_accept,prefix_accept,final_only,malformed_rejected,alias_checks");
        for(int p=0;p<2;p++) {
            long cases=0, direct=0, checked=0, only=0, malformed=0, aliases=0;
            for(int n=1;n<=2;n++) for(int ai=0;ai<(1<<n);ai++)
            for(int bi=0;bi<(int)Math.pow(3,n);bi++)
            for(int ci=0;ci<(int)Math.pow(n+1,n);ci++)
            for(int mask=0;mask<(1<<n);mask++) {
                int[] a=digits(ai,2,n), b=digits(bi,3,n), c=digits(ci,n+1,n);
                for(int i=0;i<n;i++) c[i]--;
                int[] roots=new int[Integer.bitCount(mask)]; int at=0;
                for(int i=0;i<n;i++) if((mask&(1<<i))!=0) roots[at++]=i;
                // Both orders are tested for a two-root set; empty/singleton once.
                for(int order=0;order<(roots.length==2?2:1);order++) {
                    int[] r=roots.clone(); if(order==1) { r[0]=1; r[1]=0; }
                    int[] proof=proof(a,b,c,r,p);
                    Frozen d=receive(a,b,c,r,p,null), k=receive(a,b,c,r,p,proof);
                    cases++; if(d!=null) direct++; if(k!=null) checked++;
                    if(k!=null && d==null) throw new AssertionError("unsound prefix admission");
                    if(d!=null && k==null) only++;
                    if(p==0 && ((d==null)!=(k==null))) throw new AssertionError("hereditary mismatch");
                    int[] bad=proof.clone(); bad[0]=-1;
                    if(receive(a,b,c,r,p,bad)!=null) throw new AssertionError("bad proof accepted");
                    malformed++;
                    if(d!=null) {
                        int oldA=a[0], oldB=b[0], oldC=c[0];
                        a[0]=99; b[0]=99; c[0]=99;
                        int[] rr=d.roots(); if(rr.length>0) rr[0]=99;
                        if(d.tenant(0)!=oldA || d.quota(0)!=oldB || d.next(0)!=oldC ||
                            (r.length>0 && d.roots()[0]!=r[0])) throw new AssertionError("mutable alias");
                        a[0]=oldA; b[0]=oldB; c[0]=oldC; aliases++;
                    }
                }
            }
            System.out.println((p==0?"tenant-quota":"quorum")+","+cases+","+direct+","+checked+","+only+","+malformed+","+aliases);
        }
    }
}
