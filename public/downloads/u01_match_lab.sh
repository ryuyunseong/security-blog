(
set -euo pipefail
umask 077
LAB=$(mktemp -d)
trap 'rm -rf -- "$LAB"' EXIT

ssh-keygen -q -t ed25519 -N '' -f "$LAB/host_key"
cat > "$LAB/sshd_config" <<EOF
HostKey $LAB/host_key
UsePAM no
PermitRootLogin no
Match Address 192.0.2.10
    PermitRootLogin yes
EOF

cd "$LAB"
for address in 192.0.2.11 192.0.2.10; do
    /usr/sbin/sshd -T -f ./sshd_config \
        -C "user=root,addr=$address,host=admin.example.invalid,laddr=192.0.2.20,lport=22" \
        | awk '$1 == "permitrootlogin"'
done
)
